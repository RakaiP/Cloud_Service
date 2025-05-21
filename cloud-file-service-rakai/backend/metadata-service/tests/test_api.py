import pytest
import uuid
from app.main import health_check
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging

# Configure logging to see what's happening in tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment (use in-memory SQLite for tests regardless of environment)
DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables once for all tests
Base.metadata.create_all(bind=test_engine)

@pytest.fixture
def db():
    """Fixture to provide a test database session that's closed after use"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

def test_health_check():
    """Test health check endpoint directly"""
    response = health_check()
    assert response["status"] == "healthy"

@pytest.mark.timeout(5)  # Set a 5-second timeout for this test
def test_create_file(db):
    """Test creating a new file using SQLite in-memory database"""
    from app import models, schemas, crud
    
    # Create file data with the correct Pydantic model
    file_data = schemas.FileInput(filename="test_file.txt")
    
    # Call the CRUD function directly
    logger.info("Creating file in test database...")
    file = crud.create_file(db=db, file=file_data)
    
    # Assertions
    assert file.filename == "test_file.txt"
    assert file.id is not None
    
    # Verify we can retrieve the created file
    logger.info("Retrieving file from test database...")
    db_file = crud.get_file(db, file_id=file.id)
    assert db_file.filename == "test_file.txt"

@pytest.mark.timeout(5)  # Set a 5-second timeout for this test
def test_get_nonexistent_file(db):
    """Test getting a file that doesn't exist"""
    from app import crud
    
    fake_id = str(uuid.uuid4())
    logger.info(f"Looking up non-existent file with ID: {fake_id}")
    db_file = crud.get_file(db, file_id=fake_id)
    assert db_file is None
