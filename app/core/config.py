from pydantic import BaseModel, Field, validator
from functools import lru_cache
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    # Application
    PROJECT_NAME: str = "Incident Management System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/v1"
    
    # Database
    DATABASE_URL: str = Field(
        default=os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/incident_management"),
        description="Database connection string"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default=os.getenv("SECRET_KEY", "your-secret-key-here"),
        description="Secret key for JWT token generation"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Elastic APM
    ELASTIC_APM_SERVER_URL: Optional[str] = os.getenv("ELASTIC_APM_SERVER_URL")
    ELASTIC_APM_SERVICE_NAME: str = os.getenv("ELASTIC_APM_SERVICE_NAME", "incident-management")
    
    # Notification Settings
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in environment variables

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings, cached for better performance.
    """
    return Settings()
