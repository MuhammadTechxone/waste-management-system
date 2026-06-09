import os
import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query
from sqlalchemy.orm import Session # Import ReportResponse
from database import get_db
from models import Report
from schemas import ReportResponse # Import ReportResponse
from constants import SEVERITY_SCORES
from services.verification import (
    get_image_hash, check_duplicates, haversine_metres,
    count_nearby_confirmations, calculate_confidence
)

router = APIRouter(prefix="/report", tags=["reports"])

UPLOAD_DIR = "uploads"

@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_report(
    latitude: float = Form(...),
    longitude: float = Form(...),
    location_name: str = Form(...),
    description: str = Form(...),
    severity: str = Form(...),
    reporter_id: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # 0. Coordinate Validation (Spec Section 5.2)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise HTTPException(status_code=422, detail="Invalid GPS coordinates")

    # 1. Basic validation
    if severity not in SEVERITY_SCORES:
        raise HTTPException(status_code=400, detail="Invalid severity level")

    # 2. Handle Image
    img_path = None
    img_hash = None
    file_content = None
    image_small = False # Initialize image_small
    
    if image:
        file_content = await image.read()
        # Validate size (5MB)
        if len(file_content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image too large")
        
        # Validate MIME type (Spec Section 2.2) # TODO: Implement image dimension check (200x200px) and set image_small accordingly
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if image.content_type not in allowed_types:
            raise HTTPException(status_code=422, detail="Unsupported image format")

        # Implement image dimension check (200x200px) and set image_small accordingly
        if not check_image_dimensions(file_content):
            image_small = True

        img_hash = get_image_hash(file_content)
        
        # Save to disk
        today_str = date.today().isoformat()
        day_dir = os.path.join(UPLOAD_DIR, today_str)
        os.makedirs(day_dir, exist_ok=True)
        
        ext = image.filename.split(".")[-1] if "." in image.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        img_path = os.path.join(day_dir, filename)
        
        with open(img_path, "wb") as f:
            f.write(file_content)

    # 3. Verification Logic
    hash_dup, proximity_dup = check_duplicates(db, latitude, longitude, img_hash)
    confirmations = count_nearby_confirmations(db, latitude, longitude)
    
    conf_score = calculate_confidence(
        latitude, longitude, description, 
        has_image=(image is not None),
        image_small=image_small, # Pass image_small status
        hash_dup=hash_dup,
        proximity_dup=proximity_dup,
        confirmations=confirmations
    )

    # 4. Create Database Record
    new_report = Report(
        latitude=latitude, longitude=longitude,
        location_name=location_name, description=description,
        severity=severity, severity_score=SEVERITY_SCORES[severity],
        reporter_id=reporter_id, image_path=img_path, image_hash=img_hash,
        is_duplicate=(hash_dup or proximity_dup),
        confidence_score=conf_score
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    # Construct image_url only if an image was uploaded
    image_url = None
    if img_path:
        image_url = f"/uploads/{today_str}/{filename}"

    return {
        "success": True,
        "report_id": new_report.id,
        "image_url": image_url, # Return the full URL for the frontend
        "confidence_score": new_report.confidence_score,
        "state": new_report.state
    }

@router.get("/", response_model=List[ReportResponse])
async def get_reports(
    severity: Optional[str] = None,
    state: Optional[str] = None,
    exclude_resolved: bool = True,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: Optional[float] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Report)

    if severity:
        query = query.filter(Report.severity == severity)
    if state:
        states = state.split(",")
        query = query.filter(Report.state.in_(states))
    if exclude_resolved:
        query = query.filter(~Report.state.in_(["resolved", "rejected", "expired"]))

    # Fetch all matching reports to apply proximity filtering in memory
    reports = query.all()

    # Proximity Filter (Section 6.1)
    if lat is not None and lon is not None and radius_km is not None:
        radius_m = radius_km * 1000
        reports = [
            r for r in reports 
            if haversine_metres(lat, lon, r.latitude, r.longitude) <= radius_m
        ]

    # Apply pagination to the filtered list
    start = (page - 1) * limit
    return reports[start : start + limit]