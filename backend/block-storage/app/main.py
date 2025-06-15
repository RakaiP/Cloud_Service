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
import asyncio

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
    allow_methods=["*"],  # This allows OPTIONS requests
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

@app.options("/health")
async def health_check_options():
    """Handle OPTIONS preflight for health endpoint"""
    return {"message": "OK"}

@app.get("/")
async def root():
    return {"message": "Block Storage Service", "storage": "MinIO", "status": "running", "auth": "Auth0"}

@app.options("/")
async def root_options():
    """Handle OPTIONS preflight for root endpoint"""
    return {"message": "OK"}

@app.get("/chunks/{chunk_id}")
async def download_file_chunk(chunk_id: str):
    """Download a file chunk from MinIO - NO AUTH REQUIRED for downloads"""
    try:
        print(f"Downloading chunk: {chunk_id}")
        
        # Download chunk data
        chunk_data = download_chunk(chunk_id)
        print(f"Successfully downloaded chunk {chunk_id}: {len(chunk_data)} bytes")
        
        # 🚀 CRITICAL FIX: Ensure Content-Length is accurate
        actual_size = len(chunk_data)
        
        # Return as streaming response with CORRECT headers
        return StreamingResponse(
            BytesIO(chunk_data),
            media_type="application/octet-stream",
            headers={
                "Content-Length": str(actual_size),  # CRITICAL: Must match actual data
                "Cache-Control": "max-age=3600",
                "Accept-Ranges": "bytes"  # Enable range requests
            }
        )
    
    except S3Error as e:
        print(f"MinIO S3 error downloading chunk {chunk_id}: {e}")
        if "NoSuchKey" in str(e):
            raise HTTPException(status_code=404, detail="Chunk not found")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        print(f"Error downloading chunk {chunk_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.post("/chunks")
async def upload_file_chunk(
    file: UploadFile = File(...),
    chunk_id: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file chunk to MinIO (requires Auth0 authentication)"""
    try:
        print(f"Received upload request for file: {file.filename}")
        
        # Generate chunk_id if not provided
        if not chunk_id:
            chunk_id = f"{file.filename}_{uuid.uuid4().hex[:8]}"
        
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
            "bucket": MINIO_BUCKET
        }
    
    except S3Error as e:
        print(f"MinIO S3 error: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.delete("/chunks/{chunk_id}")
async def delete_file_chunk(
    chunk_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a file chunk from MinIO (requires Auth0 authentication)"""
    try:
        user_id = current_user.get("sub")
        
        # For service-to-service calls, allow deletion if chunk_id contains user_id
        # For direct user calls, require exact prefix match
        if not (chunk_id.startswith(f"{user_id}_") or user_id in chunk_id):
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
            return {"message": "Chunk not found (already deleted)", "chunk_id": chunk_id}
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.get("/chunks")
async def list_all_chunks():
    """List all chunks in MinIO bucket"""
    try:
        chunks = list_chunks()
        return {
            "bucket": MINIO_BUCKET,
            "chunks": chunks,
            "count": len(chunks)
        }
    
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")

@app.get("/stats")
async def get_storage_stats():
    """Get storage statistics"""
    try:
        chunks = list_chunks()
        return {
            "bucket": MINIO_BUCKET,
            "total_chunks": len(chunks),
            "storage_backend": "MinIO",
            "endpoint": "minio:9000"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

