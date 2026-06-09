from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import HeatmapPoint
from services.heatmap_engine import get_heatmap_points

router = APIRouter(prefix="/heatmap", tags=["heatmap"])

@router.get("/", response_model=List[HeatmapPoint])
async def get_heatmap(
    min_confidence: int = Query(40, ge=0, le=100, description="Minimum confidence score (0-100)"),
    max_age_days: int = Query(14, ge=1, description="Exclude reports older than N days"),
    include_resolved: bool = Query(False, description="Include resolved reports at 10% weight"),
    db: Session = Depends(get_db)
):
    """
    Returns weighted coordinates for heatmap visualization (Spec Section 2.3).
    Weights are derived from severity scores and filtered by confidence and age.
    """
    return get_heatmap_points(db, min_confidence, max_age_days, include_resolved)