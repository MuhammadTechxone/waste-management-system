from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re

class ReportBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    location_name: str = Field(..., min_length=1, max_length=200, description="Name of location")
    description: str = Field(..., min_length=10, max_length=1000, description="Detailed description of waste issue")
    severity: str = Field(..., description="Severity level: Low, Medium, High, or Critical")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        """Ensure severity is one of the allowed values."""
        allowed_severities = {"Low", "Medium", "High", "Critical"}
        if v not in allowed_severities:
            raise ValueError(f"Severity must be one of {allowed_severities}")
        return v
    
    @field_validator('location_name')
    @classmethod
    def validate_location_name(cls, v):
        """Sanitize location name: alphanumeric, spaces, common punctuation only."""
        if not re.match(r"^[a-zA-Z0-9\s,.\-()]*$", v):
            raise ValueError("Location name contains invalid characters")
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Sanitize description: prevent extreme whitespace, validate length."""
        v = " ".join(v.split())  # Normalize whitespace
        if len(v) < 10:
            raise ValueError("Description must be at least 10 characters")
        return v

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
