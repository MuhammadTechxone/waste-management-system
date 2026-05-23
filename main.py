from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import models
from api import reports, heatmap, admin, analytics, alerts
from database import engine, SessionLocal
from services.state_manager import expire_stale_reports
from datetime import datetime

# Create database tables
models.Base.metadata.create_all(bind=engine)

ALLOWED_ORIGINS = [
    # Replace with your actual HF Space production URLs as per Spec 1.3
    "https://user-facing-frontend.hf.space",
    "https://admin-dashboard.hf.space",
    "http://localhost:3000",
    "http://localhost:8501",
    "http://127.0.0.1:5500", # Standard VS Code Live Server port
    "http://localhost:5500",
    "file:///C:/mental_real_copy/index.html",
    "null", 
]

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
    try:
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