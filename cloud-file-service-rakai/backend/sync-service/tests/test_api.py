import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import os

from app.main import app
from app.database import Base, get_db
from app import models

# Get database URL from environment (will use PostgreSQL in Docker, SQLite as fallback)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")

# Create test engine
test_engine = create_engine(
    DATABASE_URL,
    # Only use these connect_args for SQLite
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client - fix initialization by using the correct parameter
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=test_engine)

def test_root_endpoint():
    """Test root endpoint returns API information"""
    response = client.get("/")
    assert response.status_code == 200
    assert "title" in response.json()
    assert "version" in response.json()

def test_create_sync_event():
    """Test creating a sync event"""
    test_file_id = str(uuid.uuid4())
    response = client.post(
        "/sync-events",
        json={
            "file_id": test_file_id,
            "event_type": "upload"
        }
    )
    assert response.status_code == 200
    assert "event_id" in response.json()
    assert "message" in response.json()
    
    # Verify that the event was created
    event_id = response.json()["event_id"]
    response = client.get(f"/sync-events/{event_id}")
    assert response.status_code == 200
    assert response.json()["file_id"] == test_file_id
    assert response.json()["event_type"] == "upload"
