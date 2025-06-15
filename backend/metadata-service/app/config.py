from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./metadata.db")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    API_PREFIX: str = "/api/v1"
    APP_NAME: str = "Metadata Service"
    APP_VERSION: str = "0.1.9"
    
    # Auth0 settings - with default values to prevent startup issues
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
    API_AUDIENCE: str = os.getenv("API_AUDIENCE", "")
    ALGORITHMS: str = os.getenv("ALGORITHMS", "RS256")
    
    # ✅ ADD: Auth0 Management API settings (required for user search)
    AUTH0_MANAGEMENT_CLIENT_ID: str = os.getenv("AUTH0_MANAGEMENT_CLIENT_ID", "")
    AUTH0_MANAGEMENT_CLIENT_SECRET: str = os.getenv("AUTH0_MANAGEMENT_CLIENT_SECRET", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Only validate auth settings if they're actually needed
        if not self.AUTH0_DOMAIN and os.getenv("REQUIRE_AUTH", "true").lower() == "true":
            print("WARNING: AUTH0_DOMAIN not set - authentication will be disabled")
        if not self.API_AUDIENCE and os.getenv("REQUIRE_AUTH", "true").lower() == "true":
            print("WARNING: API_AUDIENCE not set - authentication will be disabled")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # ✅ CRITICAL FIX: Allow extra fields to prevent Pydantic validation errors
        extra = "allow"

# Create settings instance
@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()