from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings that can be loaded from environment variables."""
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./sync_service.db"
    
    # API settings
    API_TITLE: str = "Synchronization Service API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Service for handling synchronization events between client and cloud components"
    
    # Security settings
    SECRET_KEY: str = "change_this_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Service settings
    SYNC_EVENT_PROCESS_INTERVAL: int = 5  # Process events every 5 seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    """Get cached settings instance."""
    return Settings()