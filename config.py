"""
Centralized configuration with environment variable validation.
Uses Pydantic Settings for type-safe, validated configuration.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All required settings are validated on startup.
    """
    
    # API Configuration
    api_title: str = "Waste Management Monitoring System API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = Field(default="sqlite:///./reports.db")
    
    # Authentication
    admin_api_key: str = Field(..., description="Admin API key for protected endpoints")
    
    # Google AI Configuration
    google_api_key: str = Field(..., description="Google Generative AI API key")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8501",
            "http://127.0.0.1:5500",
            "http://localhost:5500",
        ],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    enable_rate_limiting: bool = True
    rate_limit_reports_per_minute: int = 10
    rate_limit_admin_per_minute: int = 100
    
    # Background Jobs
    auto_expiry_interval_hours: int = 6
    report_expiry_days: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database URL is valid."""
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")
        return v
    
    @field_validator('admin_api_key')
    @classmethod
    def validate_admin_key_length(cls, v):
        """Ensure admin key has minimum length."""
        if len(v) < 16:
            raise ValueError("ADMIN_API_KEY must be at least 16 characters (use a strong key)")
        return v
    
    @field_validator('google_api_key')
    @classmethod
    def validate_google_key(cls, v):
        """Ensure Google API key is provided."""
        if not v or v == "":
            raise ValueError("GOOGLE_API_KEY is required for image classification")
        return v

# Load settings once on startup
settings = Settings()
