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
    
    # Auth0 settings
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
    API_AUDIENCE: str = os.getenv("API_AUDIENCE", "")
    ALGORITHMS: str = os.getenv("ALGORITHMS", "RS256")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()