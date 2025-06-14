from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, Response
from .minio_client import (
    ensure_bucket, upload_chunk, download_chunk, 
    delete_chunk, list_chunks, MINIO_BUCKET
)
from minio.error import S3Error
from io import BytesIO
import uuid

app = FastAPI(
    title="Block Storage Service API",
    version="1.0.0",
    description="API for storing, retrieving, and deleting file chunks."
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
    return {"message": "Block Storage Service", "storage": "MinIO", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
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
    chunk_id: str = Form(None)
):
    """Upload a file chunk to MinIO"""
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

@app.get("/chunks/{chunk_id}")
async def download_file_chunk(chunk_id: str):
    """Download a file chunk from MinIO"""
    try:
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
async def delete_file_chunk(chunk_id: str):
    """Delete a file chunk from MinIO"""
    try:
        delete_chunk(chunk_id)
        return {
            "message": "Chunk deleted successfully",
            "chunk_id": chunk_id,
            "bucket": MINIO_BUCKET
        }
    
    except S3Error as e:
        if "NoSuchKey" in str(e):
            raise HTTPException(status_code=404, detail="Chunk not found")
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
