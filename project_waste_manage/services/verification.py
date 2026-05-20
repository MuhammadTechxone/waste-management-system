import hashlib
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Report

PROXIMITY_METRES = 50
RECENCY_HOURS = 24
CONFIRMATION_RADIUS_M = 200
CONFIRMATION_HOURS = 48

def haversine_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Standard haversine formula for distance in metres."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def get_image_hash(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()

def check_duplicates(db: Session, lat: float, lon: float, img_hash: str = None):
    """Flags exact image matches or reports within 50m and 24h."""
    hash_dup = False
    if img_hash:
        hash_dup = db.query(Report).filter(Report.image_hash == img_hash).count() > 0
    
    cutoff = datetime.utcnow() - timedelta(hours=RECENCY_HOURS)
    recent = db.query(Report).filter(
        Report.created_at >= cutoff,
        Report.is_duplicate == False,
        Report.state != "rejected"
    ).all()
    
    proximity_dup = any(
        haversine_metres(lat, lon, r.latitude, r.longitude) <= PROXIMITY_METRES
        for r in recent
    )
    return hash_dup, proximity_dup

def count_nearby_confirmations(db: Session, lat: float, lon: float) -> int:
    """Counts active reports within 200m and 48h to boost confidence."""
    cutoff = datetime.utcnow() - timedelta(hours=CONFIRMATION_HOURS)
    nearby = db.query(Report).filter(
        Report.created_at >= cutoff,
        Report.state != "rejected"
    ).all()
    
    return sum(1 for r in nearby if haversine_metres(lat, lon, r.latitude, r.longitude) <= CONFIRMATION_RADIUS_M)

def calculate_confidence(lat, lon, description, has_image, hash_dup, proximity_dup, confirmations) -> int:
    """Computes confidence score (0-100) based on Spec Section 5.1."""
    score = 50
    if has_image: score += 20
    if hash_dup: score -= 30
    if proximity_dup: score -= 25
    if len(description) < 10: score -= 10
    if not (-90 <= lat <= 90 and -180 <= lon <= 180): score -= 50
        
    # Add 15 points per confirming report, cap at 30
    confirms = min(confirmations, 2)
    score += confirms * 15
    
    return max(0, min(100, score))