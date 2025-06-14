from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging

from . import models, schemas, crud
from .database import engine, get_db
from .config import settings
from .auth import get_current_user  # Import auth dependency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create database tables"""
    try:
        logger.info("Creating database tables...")
        models.Base.metadata.drop_all(bind=engine)  # Drop existing tables
        models.Base.metadata.create_all(bind=engine)  # Create fresh tables
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

# Create tables in the database
create_tables()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # This allows OPTIONS requests
    allow_headers=["*"],
)

# Health check endpoint - public, no auth required
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.options("/health")
async def health_check_options():
    """Handle OPTIONS preflight for health endpoint"""
    return {"message": "OK"}

@app.get("/")
async def root():
    return {"status": "Metadata Service is running", "service": "metadata-service"}

@app.options("/")
async def root_options():
    """Handle OPTIONS preflight for root endpoint"""
    return {"message": "OK"}

# File endpoints - protected
@app.post("/files", response_model=schemas.File, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
def create_file(file: schemas.FileInput, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Create a new file metadata entry
    """
    try:
        logger.info(f"Creating file: {file.filename} for user: {current_user.get('sub', 'unknown')}")
        result = crud.create_file(db=db, file=file)
        logger.info(f"File created successfully with ID: {result.file_id}")
        return result
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")


@app.get("/files/{file_id}", response_model=schemas.File, dependencies=[Depends(get_current_user)])
def read_file(file_id: str, db: Session = Depends(get_db)):
    """
    Get file metadata by file_id
    """
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file


@app.get("/files", response_model=List[schemas.File], dependencies=[Depends(get_current_user)])
def read_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get list of files with pagination
    """
    files = crud.get_files(db, skip=skip, limit=limit)
    return files


@app.put("/files/{file_id}", response_model=schemas.File, dependencies=[Depends(get_current_user)])
def update_file(file_id: str, file: schemas.FileInput, db: Session = Depends(get_db)):
    """
    Update file metadata
    """
    db_file = crud.update_file(db, file_id=file_id, file_data=file)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file


@app.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
def delete_file(file_id: str, db: Session = Depends(get_db)):
    """
    Delete a file by ID
    """
    result = crud.delete_file(db, file_id=file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    return JSONResponse(status_code=204, content={})


# Version endpoints - protected
@app.post("/files/{file_id}/versions", response_model=schemas.FileVersion, dependencies=[Depends(get_current_user)])
def create_version(file_id: str, version: schemas.VersionCreate, db: Session = Depends(get_db)):
    """
    Create a new version for a file
    """
    # Check if file exists
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Create version
    return crud.create_file_version(db=db, version=version)


@app.get("/files/{file_id}/versions", response_model=List[schemas.FileVersion], dependencies=[Depends(get_current_user)])
def read_versions(file_id: str, db: Session = Depends(get_db)):
    """
    Get all versions of a file
    """
    # Check if file exists
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get versions
    versions = crud.get_file_versions(db, file_id=file_id)
    return versions


# Chunk endpoints - protected
@app.post("/files/{file_id}/chunks", response_model=schemas.FileChunk, dependencies=[Depends(get_current_user)])
def create_chunk(file_id: str, chunk: schemas.ChunkCreate, db: Session = Depends(get_db)):
    """
    Create a new chunk for a file
    """
    # Check if file exists
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Create chunk
    return crud.create_file_chunk(db=db, chunk=chunk)


@app.get("/files/{file_id}/chunks", response_model=List[schemas.FileChunk], dependencies=[Depends(get_current_user)])
def read_chunks(file_id: str, db: Session = Depends(get_db)):
    """
    Get all chunks of a file
    """
    # Check if file exists
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get chunks
    chunks = crud.get_file_chunks(db, file_id=file_id)
    return chunks