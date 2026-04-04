# CompanyLens
An AI-driven research assistant designed to prepare candidates for interviews by conducting deep-dive company analysis and scheduling preparation alerts in real-time.

## Project Goal
The primary goal of this agent is to reduce the "manual research" overhead for job seekers. It orchestrates multiple specialized sub-agents to analyze a company's market position, technical stack, and cultural values simultaneously, while using the **Model Context Protocol (MCP)** to bridge the gap between AI insights and personal productivity tools like Google Calendar.

## How it Works
1.  **User Input**: Receives a company name, target role, and interview date.
2.  **Orchestration Phase**: A primary "Planner" agent generates a high-level research strategy.
3.  **Parallel Execution**: 
    * **Market Agent**: Researches competitors and market trends.
    * **Tech Agent**: Identifies core technology stacks and product launches.
    * **Culture Agent**: Analyzes company values and interview themes.
    * **MCP Tool**: Calculates the optimal prep time (24h before) and injects a calendar event.
4.  **State Management**: All research data and action logs are persisted in **Google Cloud Firestore**.
5.  **Minimalist UI**: Delivers insights through a clean, distraction-free "White UI" focused on readability.

## Tech Stack
* **Backend**: FastAPI (Python 3.10+)
* **LLM**: Google Gemini 2.5 Flash
* **Database**: Google Cloud Firestore
* **Protocols**: Model Context Protocol (MCP) for tool-use integration.
* **APIs**: Google Calendar API (v3)
* **Frontend**: Vanilla JS, HTML5, CSS3 (Inter Font Family)
* **Deployment**: Optimized for Google Cloud Run

## Project Structure
```text
interview-orchestrator/
- main.py              # Entry point & FastAPI initialization
- api/
   - routes.py        # API Endpoints & Request Orchestration
- core/
   - agents.py        # Sub-agent logic & Gemini prompt engineering
   - mcp_tools.py     # Calendar integration & MCP tool definitions
- static/
   - index.html       # Minimalist Frontend UI
- requirements.txt     # Dependency management
- service-account.json # GCP Credentials (local only)
