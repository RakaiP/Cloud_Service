from sqlalchemy import Column, Integer, String, Enum, DateTime, Text
from sqlalchemy.sql import func
import enum
import uuid

from app.database import Base


class EventType(str, enum.Enum):
    """Enumeration of sync event types."""
    UPLOAD = "upload"
    DELETE = "delete"
    UPDATE = "update"


class EventStatus(str, enum.Enum):
    """Enumeration of sync event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncEvent(Base):
    """SQLAlchemy model for sync events."""
    __tablename__ = "sync_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    status = Column(String, index=True, default=EventStatus.PENDING)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())