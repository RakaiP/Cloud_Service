from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .auth import get_current_user
from .chunker import FileChunker
from .services import ServiceIntegration
import os
import logging
from typing import Dict, Any
import tempfile
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chunker Service API",
    version="1.0.0",
    description="Service for chunking files and coordinating with storage and metadata services"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "1048576"))  # 1MB
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "1073741824"))  # 1GB

@app.get("/")
async def root():
    return {
        "message": "Chunker Service",
        "status": "running",
        "auth": "Auth0",
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "max_file_size": MAX_FILE_SIZE
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "chunker-service",
        "version": "1.0.0"
    }

@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and chunk a file
    
    This endpoint:
    1. Receives file from frontend
    2. Creates file metadata
    3. Chunks the file
    4. Uploads chunks to block storage
    5. Updates metadata with chunk information
    6. Indexes the file for search
    """
    try:
        user_id = current_user.get("sub")
        
        # Extract the Bearer token from the request
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        access_token = auth_header.split(" ")[1]
        logger.info(f"Using token: {access_token[:20]}...")  # Log first 20 chars
        
        # Initialize chunker
        chunker = FileChunker(chunk_size=DEFAULT_CHUNK_SIZE)
        
        # Get file information first
        file_info = await chunker.get_file_info(file)
        
        # Check file size limit
        if file_info["size"] > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE} bytes"
            )
        
        logger.info(f"User {user_id} uploading file: {file_info['filename']} ({file_info['size']} bytes)")
        
        # Create a temporary file to handle the upload data
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Read all file data and write to temp file
            file_content = await file.read()
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Initialize service integration with the actual user token
            services = ServiceIntegration(access_token)
            
            # Test the token first with a simple call
            logger.info("Testing metadata service connection...")
            
            # Create file metadata
            logger.info(f"Creating file metadata for: {file_info['filename']}")
            file_metadata = await services.create_file_metadata(file_info["filename"])
            file_id = file_metadata["file_id"]
            
            logger.info(f"Created file metadata with ID: {file_id}")
            
            # Process chunks in background
            background_tasks.add_task(
                process_file_chunks_from_content,
                file_content,
                file_id,
                user_id,
                file_info,
                services,
                chunker
            )
            
            return {
                "message": "File upload initiated",
                "file_id": file_id,
                "filename": file_info["filename"],
                "size": file_info["size"],
                "num_chunks": file_info["num_chunks"],
                "status": "processing"
            }
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_file_chunks_from_content(
    file_content: bytes,
    file_id: str,
    user_id: str,
    file_info: Dict[str, Any],
    services: ServiceIntegration,
    chunker: FileChunker
):
    """Background task to process file chunks from file content"""
    try:
        logger.info(f"Starting chunk processing for file {file_id}")
        
        chunks_data = []
        chunk_metadata = []
        
        # Process file content in chunks
        total_size = len(file_content)
        chunk_size = chunker.chunk_size
        chunk_index = 0
        
        for i in range(0, total_size, chunk_size):
            chunk_data = file_content[i:i + chunk_size]
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            
            logger.info(f"Processing chunk {chunk_index} for file {file_id}")
            
            # Generate unique chunk ID
            chunk_id = f"{user_id}_{file_id}_chunk_{chunk_index}_{chunk_hash[:8]}"
            
            # Upload chunk to block storage
            storage_result = await services.upload_chunk_to_storage(chunk_data, chunk_id)
            
            # Create chunk metadata
            chunk_meta = await services.create_chunk_metadata(
                file_id,
                chunk_index,
                storage_result.get("chunk_id", chunk_id)
            )
            
            chunks_data.append(chunk_data)
            chunk_metadata.append(chunk_meta)
            
            logger.info(f"Successfully processed chunk {chunk_index}")
            chunk_index += 1
        
        # Calculate file hash
        file_hash = chunker.calculate_file_hash(chunks_data)
        
        # Create file version
        version_result = await services.create_file_version(
            file_id,
            f"chunked_file_{len(chunk_metadata)}_chunks"
        )
        
        # Index the file
        index_result = await services.index_file(
            file_id,
            file_info["filename"],
            file_info["content_type"],
            file_info["size"],
            file_hash
        )
        
        logger.info(f"Successfully processed file {file_id} with {len(chunk_metadata)} chunks")
        
    except Exception as e:
        logger.error(f"Error processing chunks for file {file_id}: {e}")

@app.get("/files/{file_id}/status")
async def get_file_status(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the processing status of a file"""
    # This would typically check the metadata service for file status
    # For now, we'll return a simple response
    return {
        "file_id": file_id,
        "status": "completed",  # In reality, this would be dynamic
        "message": "File processing completed successfully"
    }

@app.post("/reconstruct/{file_id}")
async def reconstruct_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Reconstruct a file from its chunks
    This would be used for downloads
    """
    try:
        user_id = current_user.get("sub")
        
        # This is a placeholder - in reality, you would:
        # 1. Get chunk metadata from metadata service
        # 2. Download chunks from block storage
        # 3. Reconstruct the file
        # 4. Return the reconstructed file
        
        return {
            "message": "File reconstruction not yet implemented",
            "file_id": file_id,
            "user": user_id
        }
        
    except Exception as e:
        logger.error(f"Reconstruction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reconstruction failed: {str(e)}")

@app.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Get chunker service statistics"""
    return {
        "service": "chunker-service",
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "max_file_size": MAX_FILE_SIZE,
        "user": current_user.get("sub")
    }
