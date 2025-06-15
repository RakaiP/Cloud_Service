from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import time

from .config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine instance - but don't test connection immediately
engine = None
SessionLocal = None

def initialize_database():
    """Initialize database connection with retry logic"""
    global engine, SessionLocal
    
    if engine is not None:
        return engine
    
    max_retries = 30  # Wait up to 5 minutes
    retry_delay = 10  # 10 seconds between retries
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})")
            logger.info(f"Database URL: {settings.DATABASE_URL}")
            
            # Create engine
            engine = create_engine(
                settings.DATABASE_URL, 
                echo=settings.DEBUG,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=300,    # Recycle connections every 5 minutes
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "metadata-service"
                } if 'postgresql' in settings.DATABASE_URL else {}
            )
            
            # Test the connection
            with engine.connect() as connection:
                logger.info("✅ Database connection successful")
                
                # Create session class
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                
                return engine
                
        except Exception as e:
            logger.warning(f"❌ Database connection attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("💥 All database connection attempts failed!")
                raise Exception(f"Failed to connect to database after {max_retries} attempts: {e}")

# Create base class for SQLAlchemy models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    """Get database session with lazy initialization"""
    # Initialize database if not already done
    if engine is None:
        initialize_database()
    
    if SessionLocal is None:
        raise Exception("Database not properly initialized")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_engine():
    """Get database engine with lazy initialization"""
    if engine is None:
        initialize_database()
    return engine