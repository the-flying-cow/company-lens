# CompanyLens
An AI-driven research assistant designed to prepare candidates for interviews by conducting deep-dive company analysis and scheduling preparation alerts in real-time.

## Project Goal
The primary goal of this agent is to reduce the "manual research" overhead for job seekers. It orchestrates multiple specialized sub-agents to analyze a company's market position, technical stack, and cultural values simultaneously, while using the **Model Context Protocol (MCP)** to bridge the gap between AI insights and personal productivity tools like Google Docs, Gooogle Calendar.

## How it Works
1.  **User Input**: Receives a company name, target role, and interview date.
2.  **Orchestration Phase**: A primary "Planner" agent generates a high-level research strategy.
3.  **Parallel Execution**: 
    * **Market Agent**: Researches competitors and market trends.
    * **Tech Agent**: Identifies core technology stacks and product launches.
    * **Culture Agent**: Analyzes company values and interview themes.
    * **Role Agent**: Provides expectations and insights on the 'target role' by the company.
    * **MCP Tool**: Takes down the information from the agents and creates structured notes in Google Docs.
    * **APIs Integration**: Uses Google Drive and Google Calendar api to store the Doc in a specific Drive folder and also schedule prep in Calendar on the interview date.
4. ** 
5.  **Candidate Toolit**: Help the candidate to prepare for the interview by providing introduction script, networking script, potential questions to ask recruiter, and connect with people working in the company via LinkedIn, to get insights about the company and interview process.
   * **Networking Agent**: Generate personalized networking scripts to connect with current employees on LinkedIn, including ice-breaker questions and conversation starters.
   * **Introduction Agent**: Crafts a compelling self-introduction script tailored to the company and role, highlighting relevant skills and experiences. User makes the choice of the area and context to focus on for the script.
   * **Question Agent**: Generates a list of 3 insightful questions to ask the recruiter during the interview. The questions are tailored to the company and role, and are designed to demonstrate the candidate's interest and understanding of the company.
6. **Stategy Hub**: Provides the candidate with a comprehensive strategy for preparation, including link to resources and key questions to prepare for and strategies to approach the questions before sitting for the interview.
7.  **Minimalist UI**: Delivers insights through a clean, distraction-free "UI" focused on readability.

## Tech Stack
* **Backend**: FastAPI (Python 3.10+)
* **LLM**: Google Gemini 2.5 Flash
* **Database**: Google Cloud Firestore
* **Protocols**: Model Context Protocol (MCP) for tool-use integration - Google Docs for note-taking
* **APIs**: Google Calendar API (v3), Goigle Drive API (v3)
* **Frontend**: Vanilla JS, HTML5, CSS3 (Inter Font Family)
* **Deployment**: Optimized for Google Cloud Run

## Project Structure
```text
company-lens/
- main.py              # Entry point & FastAPI initialization
- api/
   - routes.py        # API Endpoints & Request Orchestration
- core/
   - agents.py        # Sub-agent logic & Gemini prompt engineering
   - mcp_tools.py     # Calendar integration & MCP tool definitions
   - strategy_agent.py # User preparation enhancement agent
- static/
   - index.html       # Minimalist Frontend UI
   - landing.html     # Landing page/ Home page
   - prep.html       # Preparation strategy page
   - dashboard.html    # Dashboard to view strategy agent output and insights
- requirements.txt     # Dependency management
- README.md            # Project documentation
```
