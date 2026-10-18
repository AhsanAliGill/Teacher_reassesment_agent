import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.db.session import create_db_and_tables
# Load environment variables from .env file
load_dotenv()

# Verify Google API Key is loaded
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# Import router
from .routers import slides as slides_router
from .routers import auth_router as auth_router
from .routers import assessment_router as assessment_router
from .routers import report_router as report_router

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()

# Include router
app.include_router(slides_router.router)
app.include_router(auth_router.router)
app.include_router(assessment_router.router)
app.include_router(report_router.router)
# Root endpoint
@app.get("/") 
def read_root():
    return {"message": " Teacher Dasboard API is running"}
 