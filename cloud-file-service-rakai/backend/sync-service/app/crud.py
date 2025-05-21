from sqlalchemy.orm import Session
import uuid

from app import models, schemas


def create_sync_event(db: Session, sync_event: schemas.SyncEventInput) -> models.SyncEvent:
    """
    Create a new sync event in the database.
    
    Args:
        db: Database session
        sync_event: Sync event data
        
    Returns:
        The created sync event
    """
    event_id = str(uuid.uuid4())
    db_event = models.SyncEvent(
        event_id=event_id,
        file_id=sync_event.file_id,
        event_type=sync_event.event_type,
        status=models.EventStatus.PENDING
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_sync_event(db: Session, event_id: str) -> models.SyncEvent:
    """
    Get a sync event by event ID.
    
    Args:
        db: Database session
        event_id: The event ID to look up
        
    Returns:
        The sync event or None if not found
    """
    return db.query(models.SyncEvent).filter(models.SyncEvent.event_id == event_id).first()


def get_sync_events(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    status: models.EventStatus = None
) -> list[models.SyncEvent]:
    """
    Get sync events with optional filtering by status.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional filter by event status
        
    Returns:
        List of sync events
    """
    query = db.query(models.SyncEvent)
    if status:
        query = query.filter(models.SyncEvent.status == status)
    
    return query.order_by(models.SyncEvent.created_at.desc()).offset(skip).limit(limit).all()


def update_sync_event_status(
    db: Session,
    event_id: str,
    status: models.EventStatus,
    error_message: str = None
) -> models.SyncEvent:
    """
    Update the status of a sync event.
    
    Args:
        db: Database session
        event_id: The event ID to update
        status: The new status
        error_message: Optional error message if status is FAILED
        
    Returns:
        The updated sync event or None if not found
    """
    db_event = get_sync_event(db, event_id)
    if db_event:
        db_event.status = status
        if error_message:
            db_event.error_message = error_message
        db.commit()
        db.refresh(db_event)
    return db_event