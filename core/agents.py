from google import genai
import re
from google.genai import types

# Sub-Agent Logic 
async def run_sub_agent(client, agent_name: str, task: str, company: str, tools= None):
    """Executes a specialized agent task with token limits and optional tools access."""
    prompt = f"You are the {agent_name}. Research the following for {company}: {task}. Provide 3 short key insights.No intro, no outro.Keep it under 200 words."
    
    try:
        # Define the config dictionary
        config_params = {
            "max_output_tokens": 2000,
            "temperature": 0.2
        }
        
        # Add tools to config if they are provided
        if tools:
            config_params["tools"] = tools

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config_params
        )

        clean_text = re.sub(r'\*', '', response.text).strip()
        return clean_text
    except Exception as e:
        return {agent_name: f"Agent Error: {str(e)}"}