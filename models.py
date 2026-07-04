from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, func
from database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    image_hash = Column(String, nullable=True, index=True)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    waste_type = Column(String, nullable=True)
    ai_classification = Column(String, nullable=True)
    ai_significance_score = Column(Integer, nullable=True)
    
    severity = Column(String, nullable=False)
    severity_score = Column(Integer, default=20)
    
    state = Column(String, default="reported")
    confidence_score = Column(Integer, default=50)
    
    is_duplicate = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())