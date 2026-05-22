from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import Report

def get_heatmap_points(db: Session, min_confidence: int, max_age_days: int, include_resolved: bool):
    """
    Prepares weighted heatmap data based on Spec Section 2.3 and Section 10.
    """
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)
    
    # 1. Fetch relevant reports
    query = db.query(Report).filter(
        Report.confidence_score >= min_confidence,
        Report.created_at >= cutoff,
        Report.state != "rejected",
        Report.is_duplicate == False
    )
    
    reports = query.all()
    heatmap_data = []
    
    for r in reports:
        # 2. Calculate Base Weight from Severity
        weight = float(r.severity_score)
        
        # 3. Apply operational modifiers
        if r.state == "resolved":
            if not include_resolved:
                continue
            weight *= 0.1  # Resolved reports weigh 10%
            
        heatmap_data.append({
            "lat": r.latitude,
            "lon": r.longitude,
            "weight": round(weight, 2)
        })
        
    return heatmap_data