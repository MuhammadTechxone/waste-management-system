import hashlib
import math
from datetime import datetime, timedelta
import io # Added import for io
from sqlalchemy.orm import Session
from constants import SEVERITY_SCORES
from models import Report

PROXIMITY_METRES = 50
RECENCY_HOURS = 24

def haversine_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Standard haversine formula returning distance in metres."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def get_image_hash(file_bytes: bytes) -> str:
    """Generates MD5 hash for image duplicate detection."""
    return hashlib.md5(file_bytes).hexdigest()

def check_duplicates(db: Session, lat: float, lon: float, img_hash: str = None):
    """Checks for both hash and proximity duplicates (Spec Section 4)."""
    hash_dup = False
    proximity_dup = False

    if img_hash:
        hash_dup = db.query(Report).filter(Report.image_hash == img_hash).count() > 0

    cutoff = datetime.utcnow() - timedelta(hours=RECENCY_HOURS)
    recent_reports = db.query(Report).filter(
        Report.created_at >= cutoff,
        Report.state != "rejected",
        Report.latitude.between(lat - 0.001, lat + 0.001), # ~100m square
        Report.longitude.between(lon - 0.001, lon + 0.001)
    ).all()

    for r in recent_reports:
        if haversine_metres(lat, lon, r.latitude, r.longitude) <= PROXIMITY_METRES:
            proximity_dup = True
            break

    return hash_dup, proximity_dup

def count_nearby_confirmations(db: Session, lat: float, lon: float) -> int:
    """Counts reports within 200m/48h to boost confidence (Spec Section 5.1)."""
    cutoff = datetime.utcnow() - timedelta(hours=48)
    nearby = db.query(Report).filter(
        Report.created_at >= cutoff,
        Report.state != "rejected",
        Report.latitude.between(lat - 0.002, lat + 0.002), # ~200m square
        Report.longitude.between(lon - 0.002, lon + 0.002)
    ).all()
    
    count = 0
    for r in nearby: # Removed current_report_id as it's not available at this stage
        if haversine_metres(lat, lon, r.latitude, r.longitude) <= 200:
            count += 1
    return count

def calculate_confidence( # Added image_small parameter
    lat: float, lon: float, description: str,
    has_image: bool, image_small: bool, hash_dup: bool, proximity_dup: bool,
    confirmations: int, user_severity: str, ai_result: dict = None
) -> int:
    """Applies the scoring formula from Spec Section 5.1."""
    score = 50 # Base
    
    if has_image: 
        score += 20
    
    # Nigerian Context: High priority for drainage issues
    if "drain" in description.lower() or "block" in description.lower():
        score += 10
    
    if ai_result:
        # AI Confirmation: AI agrees it's valid waste
        if ai_result.get("is_valid_waste"): score += 20
        
        # AI Conflict logic: 
        # If user severity is 'Critical' (100) but AI score is low (< 30)
        user_val = SEVERITY_SCORES.get(user_severity, 20)
        if user_val >= 80 and ai_result.get("significance_score", 0) < 30:
            score -= 30  # Major Conflict Penalty

    if image_small: score -= 5 # Apply penalty for small image
    if hash_dup: score -= 30
    if proximity_dup: score -= 25
    if len(description) < 10: score -= 10
    
    # Coordinate range check is already in API layer, but safety check:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        score -= 50

    confirm_boost = min(confirmations, 2) * 15
    score += int(confirm_boost)
    
    return max(0, min(100, score))

# Helper function to check image dimensions (to be called from api/reports.py)
def check_image_dimensions(image_bytes: bytes, min_width: int = 200, min_height: int = 200) -> bool:
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        return img.width >= min_width and img.height >= min_height
    except ImportError:
        print("Pillow not installed. Cannot check image dimensions.")
        return True # Assume valid if Pillow is not available
    except Exception as e:
        print(f"Error checking image dimensions: {e}")
        return False