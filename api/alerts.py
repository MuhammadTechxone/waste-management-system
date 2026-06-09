from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Report
from services.clustering import cluster_reports
from services.verification import haversine_metres
from constants import SEVERITY_SCORES

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/")
async def get_alerts(
    severity_min: str = Query("High", description="Minimum severity to trigger alert"),
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: float = Query(5.0, description="Radius for proximity filtering"),
    db: Session = Depends(get_db)
):
    # 1. Fetch active, unresolved reports
    reports = db.query(Report).filter(
        ~Report.state.in_(["resolved", "rejected", "expired"])
    ).all()
    
    # 2. Run clustering to identify hotspots
    clusters = cluster_reports(reports)
    
    alerts = []
    threshold_score = SEVERITY_SCORES.get(severity_min, 80)
    
    for cluster in clusters:
        # Filter by severity threshold
        if cluster["max_severity"] >= threshold_score:
            
            # Optional proximity filter
            if lat is not None and lon is not None:
                dist = haversine_metres(lat, lon, cluster["centroid_lat"], cluster["centroid_lon"])
                if dist > radius_km * 1000:
                    continue
            
            alerts.append({
                "alert_type": "Environmental Risk Hotspot",
                "message": f"Significant waste accumulation ({cluster['size']} reports) detected.",
                "centroid": {"lat": cluster["centroid_lat"], "lon": cluster["centroid_lon"]},
                "severity_score": cluster["max_severity"]
            })
            
    return alerts