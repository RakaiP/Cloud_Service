from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from typing import List

from app import crud, models, schemas
from app.database import engine, get_db
from app.config import get_settings
from app.auth import get_current_user
from app.sync_processor import SyncProcessor

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

# Add CORS middleware - IMPORTANT: This must be added BEFORE other routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # This allows OPTIONS requests
    allow_headers=["*"],
)


# Background task to process sync events
async def process_sync_event(event_id: str, auth_token: str):
    """
    Process a sync event in the background with real synchronization logic.
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
        
        # Initialize sync processor with auth token
        sync_processor = SyncProcessor(auth_token)
        
        # Process based on event type
        if event.event_type == models.EventType.UPLOAD:
            result = await sync_processor.process_upload_sync(event.file_id, event_id)
            
        elif event.event_type == models.EventType.DELETE:
            result = await sync_processor.process_delete_sync(event.file_id, event_id)
            
        elif event.event_type == models.EventType.UPDATE:
            result = await sync_processor.process_update_sync(event.file_id, event_id)
        
        # Mark as completed
        crud.update_sync_event_status(db, event_id, models.EventStatus.COMPLETED)
        logger.info(f"Successfully processed sync event {event_id}: {result}")
        
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a synchronization event with real processing.
    """
    # Extract the Bearer token from the request
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    access_token = auth_header.split(" ")[1]
    user_id = current_user.get("sub")
    
    logger.info(f"User {user_id} creating sync event for file {sync_event.file_id}")
    
    # Create the sync event in the database
    db_event = crud.create_sync_event(db, sync_event)
    
    # Start background processing with auth token
    background_tasks.add_task(process_sync_event, db_event.event_id, access_token)
    
    # Return response
    return schemas.SyncEventResponse(
        message=f"Sync event for {sync_event.event_type} received and being processed",
        event_id=db_event.event_id
    )


@app.options("/sync-events")
async def sync_events_options():
    """Handle OPTIONS preflight for sync-events endpoint"""
    return {"message": "OK"}

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


@app.options("/sync-events/{event_id}")
async def sync_event_options():
    """Handle OPTIONS preflight for individual sync event endpoint"""
    return {"message": "OK"}

@app.options("/sync-events/{file_id}/status")
async def sync_status_options():
    """Handle OPTIONS preflight for sync status endpoint"""
    return {"message": "OK"}

@app.get("/sync-events/{event_id}", response_model=schemas.SyncEventDB, tags=["Sync"], dependencies=[Depends(get_current_user)])
async def get_sync_event(event_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific sync event by ID.
    """
    db_event = crud.get_sync_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Sync event not found")
    return db_event


@app.get("/sync-events/{file_id}/status", response_model=dict, tags=["Sync"], dependencies=[Depends(get_current_user)])
async def get_file_sync_status(file_id: str, db: Session = Depends(get_db)):
    """
    Get sync status for a specific file.
    """
    # Get recent sync events for this file
    events = db.query(models.SyncEvent).filter(
        models.SyncEvent.file_id == file_id
    ).order_by(models.SyncEvent.created_at.desc()).limit(10).all()
    
    if not events:
        return {
            "file_id": file_id,
            "sync_status": "no_events",
            "message": "No sync events found for this file"
        }
    
    latest_event = events[0]
    
    return {
        "file_id": file_id,
        "sync_status": latest_event.status,
        "latest_event_type": latest_event.event_type,
        "latest_event_id": latest_event.event_id,
        "last_sync": latest_event.created_at,
        "total_events": len(events),
        "error_message": latest_event.error_message
    }


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

@app.options("/health")
async def health_check_options():
    """Handle OPTIONS preflight for health endpoint"""
    return {"message": "OK"}


# For running with 'python app/main.py'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)