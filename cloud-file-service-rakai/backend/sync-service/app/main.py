from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from typing import List

from app import crud, models, schemas
from app.database import engine, get_db
from app.config import get_settings
from app.auth import get_current_user  # Import auth dependency

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)


# Background task to process sync events
def process_sync_event(event_id: str):
    """
    Process a sync event in the background.
    In a real implementation, this would handle the actual synchronization logic.
    """
    # Get a new db session for this background task
    db = next(get_db())
    
    try:
        # Update status to processing
        event = crud.update_sync_event_status(db, event_id, models.EventStatus.PROCESSING)
        if not event:
            logger.error(f"Event {event_id} not found")
            return
        
        logger.info(f"Processing sync event {event_id} of type {event.event_type} for file {event.file_id}")
        
        # Simulate processing based on event type
        if event.event_type == models.EventType.UPLOAD:
            # Logic for handling file upload sync
            logger.info(f"Handling upload sync for file {event.file_id}")
            # Simulated processing...
            
        elif event.event_type == models.EventType.DELETE:
            # Logic for handling file deletion sync
            logger.info(f"Handling deletion sync for file {event.file_id}")
            # Simulated processing...
            
        elif event.event_type == models.EventType.UPDATE:
            # Logic for handling file update sync
            logger.info(f"Handling update sync for file {event.file_id}")
            # Simulated processing...
        
        # Mark as completed
        crud.update_sync_event_status(db, event_id, models.EventStatus.COMPLETED)
        logger.info(f"Successfully processed sync event {event_id}")
        
    except Exception as e:
        # Mark as failed with error message
        error_msg = f"Error processing sync event: {str(e)}"
        logger.error(error_msg)
        crud.update_sync_event_status(db, event_id, models.EventStatus.FAILED, error_msg)
    finally:
        db.close()


@app.post("/sync-events", response_model=schemas.SyncEventResponse, tags=["Sync"], dependencies=[Depends(get_current_user)])
async def create_sync_event(
    sync_event: schemas.SyncEventInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a synchronization event.
    
    This endpoint handles sync events such as file uploads, deletions, and updates.
    """
    # Create the sync event in the database
    db_event = crud.create_sync_event(db, sync_event)
    
    # Start background processing
    background_tasks.add_task(process_sync_event, db_event.event_id)
    
    # Return response
    return schemas.SyncEventResponse(
        message=f"Sync event for {sync_event.event_type} received and being processed",
        event_id=db_event.event_id
    )


@app.get("/sync-events", response_model=List[schemas.SyncEventDB], tags=["Sync"], dependencies=[Depends(get_current_user)])
async def get_sync_events(
    skip: int = 0,
    limit: int = 100,
    status: models.EventStatus = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of sync events with optional filtering by status.
    """
    events = crud.get_sync_events(db, skip=skip, limit=limit, status=status)
    return events


@app.get("/sync-events/{event_id}", response_model=schemas.SyncEventDB, tags=["Sync"], dependencies=[Depends(get_current_user)])
async def get_sync_event(event_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific sync event by ID.
    """
    db_event = crud.get_sync_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Sync event not found")
    return db_event


@app.get("/")
async def root():
    """
    Root endpoint that returns basic API information.
    """
    return {
        "title": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "sync-service",
        "version": settings.API_VERSION
    }


# For running with 'python app/main.py'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)