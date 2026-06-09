from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import verify_admin
from services.analytics_engine import get_dashboard_stats

router = APIRouter(prefix="/admin/analytics", tags=["administration"])

@router.get("/")
async def get_analytics(
    db: Session = Depends(get_db),
    _ = Depends(verify_admin)
):
    return get_dashboard_stats(db)