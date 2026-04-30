from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from api.routes import router as api_router

from starlette.middleware.sessions import SessionMiddleware

import os
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="Interview Orchestrator")
app.mount("/static", StaticFiles(directory="static"), name="static")

is_production = os.environ.get("ENV") == "production"
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET"), https_only=True, same_site="lax")

app.include_router(api_router)
    
