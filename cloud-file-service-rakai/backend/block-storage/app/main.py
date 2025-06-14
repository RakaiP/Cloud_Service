from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from .minio_client import (
    ensure_bucket, upload_chunk, download_chunk, 
    delete_chunk, list_chunks, MINIO_BUCKET
)
from .auth import get_current_user
from minio.error import S3Error
from io import BytesIO
import uuid

app = FastAPI(
    title="Block Storage Service API",
    version="1.0.0",
    description="API for storing, retrieving, and deleting file chunks with Auth0 authentication."
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize MinIO bucket on startup"""
    try:
        print("Initializing MinIO connection...")
        ensure_bucket()
        print("Block Storage Service started successfully with MinIO")
    except Exception as e:
        print(f"Failed to initialize MinIO: {e}")
        print("Check if MinIO service is running and accessible")
        # Don't raise here to allow service to start for debugging

@app.get("/")
async def root():
    return {"message": "Block Storage Service", "storage": "MinIO", "status": "running", "auth": "Auth0"}

@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)"""
    try:
        # Test MinIO connection by listing buckets
        from .minio_client import minio_client
        buckets = minio_client.list_buckets()
        return {
            "status": "healthy", 
            "storage": "MinIO", 
            "bucket": MINIO_BUCKET,
            "minio_buckets": [b.name for b in buckets]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "MinIO connection failed"
        }

@app.post("/chunks")
async def upload_file_chunk(
    file: UploadFile = File(...),
    chunk_id: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file chunk to MinIO (requires Auth0 authentication)"""
    try:
        user_id = current_user.get("sub")  # Auth0 subject identifier
        print(f"User {user_id} uploading file: {file.filename}")
        
        # Generate chunk_id if not provided, include user_id for isolation
        if not chunk_id:
            chunk_id = f"{user_id}_{file.filename}_{uuid.uuid4().hex[:8]}"
        else:
            # Prefix with user_id to prevent cross-user access
            chunk_id = f"{user_id}_{chunk_id}"
        
        print(f"Using chunk_id: {chunk_id}")
        
        # Read file data
        data = await file.read()
        print(f"File size: {len(data)} bytes")
        
        # Upload to MinIO
        print("Uploading to MinIO...")
        upload_chunk(chunk_id, data)
        print("Upload successful!")
        
        return {
            "message": "Chunk uploaded successfully",
            "chunk_id": chunk_id,
            "size": len(data),
            "bucket": MINIO_BUCKET,
            "uploaded_by": user_id
        }
    
    except S3Error as e:
        print(f"MinIO S3 error: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/chunks/{chunk_id}")
async def download_file_chunk(
    chunk_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download a file chunk from MinIO (requires Auth0 authentication)"""
    try:
        user_id = current_user.get("sub")
        
        # Ensure user can only access their own chunks
        if not chunk_id.startswith(f"{user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied to this chunk")
        
        # Download chunk data
        chunk_data = download_chunk(chunk_id)
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(chunk_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={chunk_id}"}
        )
    
    except S3Error as e:
        if "NoSuchKey" in str(e):
            raise HTTPException(status_code=404, detail="Chunk not found")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.delete("/chunks/{chunk_id}")
async def delete_file_chunk(
    chunk_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a file chunk from MinIO (requires Auth0 authentication)"""
    try:
        user_id = current_user.get("sub")
        
        # Ensure user can only delete their own chunks
        if not chunk_id.startswith(f"{user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied to this chunk")
        
        delete_chunk(chunk_id)
        return {
            "message": "Chunk deleted successfully",
            "chunk_id": chunk_id,
            "bucket": MINIO_BUCKET,
            "deleted_by": user_id
        }
    
    except S3Error as e:
        if "NoSuchKey" in str(e):
            raise HTTPException(status_code=404, detail="Chunk not found")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.get("/chunks")
async def list_user_chunks(current_user: dict = Depends(get_current_user)):
    """List user's chunks in MinIO bucket (requires Auth0 authentication)"""
    try:
        user_id = current_user.get("sub")
        all_chunks = list_chunks()
        # Filter chunks to only show user's chunks
        user_chunks = [chunk for chunk in all_chunks if chunk.startswith(f"{user_id}_")]
        
        return {
            "bucket": MINIO_BUCKET,
            "chunks": user_chunks,
            "count": len(user_chunks),
            "user": user_id
        }
    
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")

@app.get("/stats")
async def get_user_storage_stats(current_user: dict = Depends(get_current_user)):
    """Get user's storage statistics (requires Auth0 authentication)"""
    try:
        user_id = current_user.get("sub")
        all_chunks = list_chunks()
        user_chunks = [chunk for chunk in all_chunks if chunk.startswith(f"{user_id}_")]
        
        return {
            "bucket": MINIO_BUCKET,
            "user_chunks": len(user_chunks),
            "total_chunks": len(all_chunks),
            "storage_backend": "MinIO",
            "endpoint": "minio:9000",
            "user": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")
