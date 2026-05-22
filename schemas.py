from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReportBase(BaseModel):
    latitude: float
    longitude: float
    location_name: str
    description: str
    severity: str

class ReportResponse(ReportBase):
    id: int
    state: str
    severity_score: int
    confidence_score: int
    created_at: datetime

    class Config:
        from_attributes = True

class AdminReportResponse(ReportResponse):
    image_path: Optional[str] = None
    image_hash: Optional[str] = None
    is_duplicate: bool
    reporter_id: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class ReportUpdate(BaseModel):
    state: str = Field(..., pattern="^(reported|verified|investigating|assigned|resolved|rejected|expired)$")

class HeatmapPoint(BaseModel):
    lat: float
    lon: float
    weight: float