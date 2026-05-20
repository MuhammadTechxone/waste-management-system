from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
from database import get_db
from models import Report
from schemas import AdminReportResponse, ReportUpdate
from auth import verify_admin
from services.state_manager import validate_and_update_state

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/reports", response_model=List[AdminReportResponse])
async def get_admin_reports(
    state: Optional[str] = None,
    severity: Optional[str] = None,
    is_duplicate: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    from_date: Optional[str] = None, # ISO 8601 date string
    to_date: Optional[str] = None,   # ISO 8601 date string
    page: int = Query(1, ge=1),
    limit: int = Query(100, le=500),
    sort_by: str = Query("created_at", enum=["created_at", "severity_score", "confidence_score"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db),
    _ = Depends(verify_admin)
):
    """Returns detailed report data for the admin dashboard (Spec Section 3.1)."""
    query = db.query(Report)

    if state:
        query = query.filter(Report.state == state)
    if severity:
        query = query.filter(Report.severity == severity)
    if is_duplicate is not None:
        query = query.filter(Report.is_duplicate == is_duplicate)
    if is_verified is not None:
        if is_verified:
            query = query.filter(Report.state == "verified")
        else:
            query = query.filter(Report.state != "verified")
    if from_date:
        query = query.filter(Report.created_at >= from_date)
    if to_date:
        query = query.filter(Report.created_at <= to_date)

    # Apply sorting
    sort_column = getattr(Report, sort_by)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
        
    start = (page - 1) * limit
    return query.offset(start).limit(limit).all()

@router.patch("/report/{report_id}", response_model=AdminReportResponse)
async def update_report_state(
    report_id: int,
    update_data: ReportUpdate,
    db: Session = Depends(get_db),
    _ = Depends(verify_admin)
):
    """Updates the state of a report with transition validation (Spec Section 3.2)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        return validate_and_update_state(db, report, update_data.state)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))