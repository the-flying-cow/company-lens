import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.cloud import firestore
from google import genai
from google.genai import types

from google.oauth2.credentials import Credentials
import json

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse,RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow

from datetime import datetime, timedelta, timezone

from core.agents import run_sub_agent
from core.mcp_tools import create_interview_note, get_google_service

if os.getenv("ENV") == "development":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # Only for local dev!

router = APIRouter()

CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "project_id": os.getenv("GCP_PROJECT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": ["http://localhost:8000/callback"]
    }
}

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/calendar',
    
]

@router.get("/")
async def read_landing(request: Request):
        return FileResponse('static/landing.html')


@router.get("/login")
async def login(request: Request):

    if request.session.get('google_token'):
        return RedirectResponse(url="/lens")

    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = os.environ.get("REDIRECT_URL")
    
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='false', prompt= 'consent')
    request.session['code_verifier'] = flow.code_verifier
    return RedirectResponse(authorization_url)


@router.get("/callback")
async def callback(request: Request):
    code_verifier = request.session.get('code_verifier')
    state = request.query_params.get('state')
    
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, state=state)
    flow.redirect_uri = os.environ.get("REDIRECT_URL")
    
    flow.fetch_token(
        authorization_response=str(request.url),
        code_verifier=code_verifier 
    )
    credentials = flow.credentials
    request.session['google_token'] = credentials.to_json()

    return RedirectResponse(url="/lens")

@router.get("/lens")
async def read_dashboard(request: Request):
    token_json = request.session.get('google_token')

    if not token_json:
        return RedirectResponse(url="/login")

    return FileResponse('static/index.html')

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


# GCP Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
db = firestore.Client(project=PROJECT_ID)

class InterviewRequest(BaseModel):
    company_name: str
    target_role: str
    interview_date: str

def create_calendar_prep_event(service, company_name, doc_url, start_date, end_date):
    event = {
        'summary': f'Interview Prep: {company_name}',
        'description': f'Research Notes: {doc_url}',
        'start': {
            'date': start_date,
            'timeZone': 'UTC',
        },
        'end': {
            'date': end_date,
            'timeZone': 'UTC',
        },
        'reminders': {
            'useDefault': True,
        },
    }

    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return event_result.get('htmlLink')

@router.post("/research")
async def start_research(request: InterviewRequest, session_request: Request):
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
        
        token= session_request.session.get('google_token')

        # Run everything at once for efficiency
        results = await asyncio.gather(*agent_tasks, return_exceptions= True)
        
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

        mcp_msg= await create_interview_note(token, request.company_name, combined_insights)

        doc_url = mcp_msg.get("url")
        if doc_url:
            calendar_service= get_google_service(token, 'calendar', 'v3')
            if not calendar_service:
                return "Error: Could not authenticate with Google Calendar"
            
            interview_dt= datetime.strptime(request.interview_date, "%Y-%m-%d")
            next_day_dt= interview_dt + timedelta(days=1)
            start_str = interview_dt.strftime("%Y-%m-%d")
            end_str = next_day_dt.strftime("%Y-%m-%d")
            calendar_link = create_calendar_prep_event(calendar_service, request.company_name, doc_url, start_str, end_str)
            
        # Step D: Save state to Firestore
        state_data = {
            "company_name": request.company_name,
            "role": request.target_role,
            "status": "Complete",
            "primary_plan": research_plan,
            "detailed_analysis": combined_insights,
            "mcp_action_log": mcp_msg.get("url"),
            "created_at": firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(state_data)
        
        return {
            "status": "Success", 
            "document_id": doc_ref.id, 
            "mcp_log": mcp_msg.get("url"),
            "insights": combined_insights
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Step E: Endpoint to expose MCP status
@router.get("/mcp")
async def get_mcp_info():
    return {"mcp_status": "active", "tools_integrated": ["create_interview_note"]}