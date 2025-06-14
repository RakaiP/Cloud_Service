from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional
from datetime import datetime


class EventType(str, Enum):
    """Enumeration of sync event types."""
    UPLOAD = "upload"
    DELETE = "delete"
    UPDATE = "update"


class EventStatus(str, Enum):
    """Enumeration of sync event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncEventInput(BaseModel):
    """Pydantic schema for sync event input."""
    file_id: str = Field(..., description="Unique identifier of the file")
    event_type: EventType = Field(..., description="Type of sync event being triggered")


class SyncEventResponse(BaseModel):
    """Pydantic schema for sync event response."""
    message: str = Field("Sync event successfully received", description="Confirmation message")
    event_id: str = Field(..., description="Unique ID assigned to the received sync event")


class SyncEventDB(BaseModel):
    """Pydantic schema for sync event database model."""
    id: int
    event_id: str
    file_id: str
    event_type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)