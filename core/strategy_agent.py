import asyncio
import re
from google.genai import types

async def run_question_agent(client, company_name: str, role: str, strategy_choice: str):
    """Generates 3 insightful questions focused on role, team dynamics, and the selected focus."""
    prompt = f"""You are a Question Agent. Your task is to generate 3 insightful, non-generic questions that a candidate should ask during an interview for a {role} position at {company_name} when speaking with a {strategy_choice}.

Requirements:
- Questions should reveal role dynamics, team structure, or growth opportunities
- Avoid obvious questions like \"What's your company culture?\"
- Focus on role-specific and team-focused insights
- Format: Return exactly 3 questions, one per line, starting with \"Q1:\", \"Q2:\", \"Q3:\"

Generate the questions now:"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"max_output_tokens": 2000, "temperature": 0.8}
        )
        
        questions = []
        for line in response.text.split('\n'):
            line = re.sub(r'[#*]', '', line.strip())
            if line.startswith('Q') and ':' in line:
                question = line.split(':', 1)[1].strip()
                questions.append(question)
        
        return questions[:3]
    except Exception as e:
        return [f"Error: {str(e)}"]


async def run_introduction_agent(client, company_name: str, role: str, strategy_choice: str):
    """Generates an interview introduction script based on the selected focus."""

    focus_guidance = {
        "Name-Based": "Write a warm, values-centered introduction that emphasizes identity, motivation, and the candidate's mindset. Do not include location, sports metaphors, or unconventional standout framing.",
        "Location-Based": "Write an introduction that highlights environment, learning, and professional traits tied to the candidate's location or background. Do not include name-based identity themes, sports metaphors, or unique/outlier framing.",
        "Sports-Based": "Write an introduction using a sports-inspired metaphor to showcase teamwork, discipline, and dedication. Do not include name-based identity themes, location-based framing, or abstract standout language.",
        "Unique/Standout": "Write an introduction that feels memorable and slightly unconventional while remaining professional and growth-oriented. Do not include name-based identity themes, location-based framing, or sports metaphors."
    }

    strategy_instruction = focus_guidance.get(strategy_choice, "Write a focused introduction that matches the selected style exactly.")

    prompt = f"""You are an Introduction Agent. Generate one spoken-style interview introduction script for a candidate pursuing a {role} role at {company_name}. Use only the selected focus style: {strategy_choice}.

Requirements:
- The script should feel like a natural 40-50 second spoken introduction.
- Do NOT personalize with actual names, cities, or company-specific details.
- Use placeholders such as [Name], [Location], [Sport] where needed.
- Keep language simple, professional, and conversational.
- Return one paragraph with approximately 90-110 words.
- Follow this exact guidance and do not mix styles across categories.

Style guidance:
{strategy_instruction}

Output the final introduction script only, without headings or bullet points."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"max_output_tokens": 2000, "temperature": 0.8}
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"


async def run_networking_agent(client, company_name: str, role: str):
    """Generates a networking outreach message for the selected company and role."""

    prompt = f"""You are a Networking Agent. Create one short, friendly LinkedIn connection message for a candidate applying to a {role} position at {company_name}.

Requirements:
- Use placeholders for [Name].
- Mention the candidate is reaching out because they see the recipient at the same company in the same role.
- Keep it concise, polite, and appropriate for a connection request.
- Avoid detailed storytelling or unrelated strategy content.
- Output in few lines, no bullet points, no titles.

Return the final LinkedIn connection message only."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"max_output_tokens": 1000, "temperature": 0.7}
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"


async def orchestrate_strategy_agents(client, company_name: str, target_role: str, strategy_choice: str):
    """Orchestrator that runs all agents in parallel and combines results."""
    
    question_task = run_question_agent(client, company_name, target_role, strategy_choice)
    intro_task = run_introduction_agent(client, company_name, target_role, strategy_choice)
    networking_task = run_networking_agent(client, company_name, target_role)

    questions, introduction_script, networking_script = await asyncio.gather(
        question_task,
        intro_task,
        networking_task,
        return_exceptions=True
    )

    if isinstance(questions, Exception):
        questions = [f"Question Agent Error: {str(questions)}"]
    if isinstance(introduction_script, Exception):
        introduction_script = f"Introduction Agent Error: {str(introduction_script)}"
    if isinstance(networking_script, Exception):
        networking_script = f"Networking Agent Error: {str(networking_script)}"
    
    return {
        "company_name": company_name,
        "target_role": target_role,
        "strategy_choice": strategy_choice,
        "questions": questions,
        "introduction_script": introduction_script,
        "networking_script": networking_script
    }
