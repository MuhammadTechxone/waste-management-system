import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import models
from api import reports, heatmap, admin, analytics, alerts
from database import engine, SessionLocal
from services.state_manager import expire_stale_reports
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)

# Get production URL from Render environment if available
render_url = os.environ.get("RENDER_EXTERNAL_URL")

ALLOWED_ORIGINS = [
    "https://waste-management-system-9zjg.onrender.com",
    "http://localhost:3000",
    "http://localhost:8501",
    "http://127.0.0.1:5500", # Standard VS Code Live Server port
    "http://localhost:5500",
    "null", 
]
if render_url:
    ALLOWED_ORIGINS.append(render_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle and background tasks."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_expiry_job, "interval", hours=6)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(
    title="Waste Management Monitoring System API",
    lifespan=lifespan
)

# Mount the uploads directory to serve images at /uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False, # Set to False for better compatibility with 'null' origins
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

def auto_expiry_job():
    """Task to move stale reports to expired state (Spec Section 3.3)."""
    db = SessionLocal()
    try: # Use a new session for the background job
        count = expire_stale_reports(db)
        if count > 0:
            print(f"[{datetime.now()}] Background Job: Expired {count} reports.")
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Waste Management Monitoring API is online"}

# We will include routers here in the next step:
app.include_router(reports.router)
app.include_router(heatmap.router)
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(alerts.router)