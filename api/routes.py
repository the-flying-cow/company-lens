import os
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.cloud import firestore
from google import genai
from google.genai import types

from core.agents import run_sub_agent
from core.mcp_tools import schedule_prep_alert

router = APIRouter()

# GCP Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
CALENDAR_ID = os.getenv("CALENDAR_ID")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
db = firestore.Client(project=PROJECT_ID)

class InterviewRequest(BaseModel):
    company_name: str
    target_role: str
    interview_date: str


@router.post("/research")
async def start_research(request: InterviewRequest):
    try:
        # Step A: Initialize Firestore Document
        doc_ref = db.collection("interviews").document()
        
        # Step B: Phase 1 - High Level Plan
        plan_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Provide a 3-bullet research plan for {request.company_name} - {request.target_role}.",
            config={"max_output_tokens": 2000}
        )
        research_plan = plan_response.text

        search_tool = [types.Tool(google_search=types.GoogleSearch())]

        # Step C: Phase 2 - Parallel execution (Agents + MCP Tool)
        agent_tasks = [
            run_sub_agent(client, "Market_Agent", "Market position and top 2 competitors", request.company_name),
            run_sub_agent(client, "Tech_Agent", "Core technology stack and recent product launches", request.company_name),
            run_sub_agent(client, "Culture_Agent", "Company values and common interview themes", request.company_name),
            run_sub_agent(client, "Role_Agent", f"Analyze the {request.target_role} role at the {request.company_name}. Provide 3 general expectations from this role by the company.", request.company_name, tools=search_tool)
        ]
        
        # Trigger the MCP tool call
        mcp_task = schedule_prep_alert(request.company_name, request.interview_date)
        
        # Run everything at once for efficiency
        results, mcp_msg = await asyncio.gather(asyncio.gather(*agent_tasks, return_exceptions= True), mcp_task)
        
        # Combine insights
        agent_keys = ["market_analysis", "tech_analysis", "cultural_analysis", "role_agent"]
        combined_insights = {}
        for i,r in enumerate(results):
            key= agent_keys[i]
            if isinstance(r, Exception):
                # Handle the failure gracefully
                combined_insights[key] = {
                "status": "error",
                "data": None,
                "message": str(r)
                }
            else:
                # If run_sub_agent returns the whole response, use r.text
                text_content = r.text if hasattr(r, 'text') else str(r)
                
                combined_insights[key] = {
                    "status": "success",
                    "data": text_content 
                }

        # Step D: Save state to Firestore
        state_data = {
            "company_name": request.company_name,
            "role": request.target_role,
            "status": "Complete",
            "primary_plan": research_plan,
            "detailed_analysis": combined_insights,
            "mcp_action_log": mcp_msg,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(state_data)
        
        return {
            "status": "Success", 
            "document_id": doc_ref.id, 
            "mcp_log": mcp_msg,
            "insights": combined_insights
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# Step E: Endpoint to expose MCP status
@router.get("/mcp")
async def get_mcp_info():
    return {"mcp_status": "active", "tools_integrated": ["schedule_prep_alert"]}