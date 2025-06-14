from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine instance
try:
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    
    # Test the connection
    with engine.connect() as connection:
        logger.info("Database connection successful")
        
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    raise

# Create session class to be used for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for SQLAlchemy models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()