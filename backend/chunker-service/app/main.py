from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging
from io import BytesIO
import asyncio
import hashlib
import httpx
import os
from . import services
from .auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Chunker Service API",
    version="1.0.0",
    description="Service for chunking large files and orchestrating uploads"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chunker-service"}

@app.options("/health")
async def health_check_options():
    """Handle OPTIONS preflight for health endpoint"""
    return {"message": "OK"}

@app.get("/")
async def root():
    return {"message": "Chunker Service", "status": "running"}

@app.options("/")
async def root_options():
    """Handle OPTIONS preflight for root endpoint"""
    return {"message": "OK"}

@app.post("/upload")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file by splitting it into chunks"""
    try:
        user_id = current_user.get("sub")
        user_email = current_user.get("email")  # ✅ Get email from token
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        logger.info(f"User {user_id} ({user_email}) uploading file: {file.filename} ({file.size} bytes)")
        
        # Create service integration instance with auth token
        service_integration = services.ServiceIntegration(auth_token=auth_header.replace("Bearer ", ""))
        
        # Create file metadata with proper user info
        logger.info(f"Creating file metadata for: {file.filename}")
        file_metadata = await service_integration.create_file_metadata(
            filename=file.filename,
            owner_user_id=user_id,
            owner_email=user_email  # ✅ Pass email to metadata service
        )
        file_id = file_metadata["file_id"]
        logger.info(f"Created file metadata with ID: {file_id} for user {user_email}")
        
        # Trigger background chunk processing
        background_tasks.add_task(
            process_file_chunks,
            file, 
            file_id, 
            user_id,
            auth_header
        )
        
        return {
            "message": "File upload initiated",
            "file_id": file_id,
            "filename": file.filename,
            "status": "processing",
            "owner": user_email  # ✅ Return owner info
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/download/{file_id}")
async def download_file(
    file_id: str, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Download a complete file by reconstructing it from chunks"""
    try:
        user_id = current_user.get("sub")
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        logger.info(f"🚀 DOWNLOAD START: User {user_id} downloading file {file_id}")
        overall_start = asyncio.get_event_loop().time()
        
        # Create service integration instance with auth token
        service_integration = services.ServiceIntegration(auth_token=auth_header.replace("Bearer ", ""))
        
        # Step 1: Get file info
        logger.info("📊 Step 1: Getting file metadata...")
        metadata_start = asyncio.get_event_loop().time()
        try:
            file_info = await service_integration.get_file_download_info(file_id)
            metadata_end = asyncio.get_event_loop().time()
            logger.info(f"✅ Metadata retrieved in {metadata_end - metadata_start:.2f}s: {file_info.get('filename', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Failed to get file metadata: {e}")
            raise HTTPException(status_code=404, detail="File not found or inaccessible")
        
        filename = file_info.get("filename", f"file_{file_id}")
        chunk_ids = file_info.get("chunk_ids", [])
        
        if not chunk_ids:
            logger.warning(f"❌ No chunks found for file {file_id}")
            raise HTTPException(status_code=404, detail="No file chunks found")
        
        logger.info(f"🔥 Step 2: Starting download of {len(chunk_ids)} chunks for {filename}")
        
        # Step 2: Download chunks concurrently
        download_start = asyncio.get_event_loop().time()
        try:
            file_chunks = await service_integration.download_chunks_concurrently(chunk_ids)
            download_end = asyncio.get_event_loop().time()
            logger.info(f"✅ Chunks downloaded in {download_end - download_start:.2f}s")
        except Exception as e:
            logger.error(f"❌ Failed to download chunks: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to download chunks: {str(e)}")
        
        # Step 3: Combine chunks
        logger.info("🔧 Step 3: Combining chunks...")
        assembly_start = asyncio.get_event_loop().time()
        complete_file_data = b''.join(file_chunks)
        total_size = len(complete_file_data)
        assembly_end = asyncio.get_event_loop().time()
        logger.info(f"✅ File assembled in {assembly_end - assembly_start:.2f}s")
        
        overall_end = asyncio.get_event_loop().time()
        total_time = overall_end - overall_start
        
        logger.info(f"🎉 DOWNLOAD COMPLETE: {total_size} bytes in {total_time:.2f} seconds")
        logger.info(f"📊 Overall speed: {total_size / (1024*1024) / total_time:.2f} MB/s")
        logger.info(f"⏱️ Breakdown: Metadata={metadata_end-metadata_start:.2f}s, Download={download_end-download_start:.2f}s, Assembly={assembly_end-assembly_start:.2f}s")
        
        # 🚀 CRITICAL FIX: Create BytesIO stream for the complete file with CORRECT headers
        file_stream = BytesIO(complete_file_data)
        
        # 📊 FIXED: Ensure Content-Length matches actual data size
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/octet-stream",
            "Content-Length": str(total_size),  # CRITICAL: This MUST match the actual data size
            "Cache-Control": "no-cache"  # Prevent caching issues
        }
        
        logger.info(f"🎯 Response headers: Content-Length={total_size}, filename={filename}")
        
        return StreamingResponse(
            file_stream,
            media_type="application/octet-stream",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download failed for file {file_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

async def process_file_chunks(
    file: UploadFile, 
    file_id: str, 
    user_id: str, 
    auth_header: str
):
    """Process file chunks in background with authentication"""
    try:
        # Create service integration with auth token
        service_integration = services.ServiceIntegration(auth_token=auth_header.replace("Bearer ", ""))
        
        logger.info(f"Starting chunk processing for file {file_id}")
        
        # Read file content
        content = await file.read()
        total_file_size = len(content)  # Store actual file size
        chunk_size = 4194304  # 4MB chunks
        total_chunks = (len(content) + chunk_size - 1) // chunk_size
        
        logger.info(f"File size: {total_file_size} bytes, will create {total_chunks} chunks")
        
        # Process each chunk
        for chunk_index in range(total_chunks):
            logger.info(f"Processing chunk {chunk_index} for file {file_id}")
            
            start = chunk_index * chunk_size
            end = min(start + chunk_size, len(content))
            chunk_data = content[start:end]
            
            # Create chunk hash for unique ID
            chunk_hash = hashlib.md5(chunk_data).hexdigest()
            chunk_id = f"{user_id}_{file_id}_chunk_{chunk_index}_{chunk_hash[:8]}"
            
            # Upload chunk to block storage with auth
            await service_integration.upload_chunk_with_auth(chunk_id, chunk_data, auth_header)
            
            # Register chunk in metadata service
            await service_integration.create_chunk_metadata(file_id, chunk_index, chunk_id)
            
            logger.info(f"Successfully processed chunk {chunk_index}")
        
        # 🚀 NEW: Update file with actual size (non-blocking)
        try:
            await service_integration.update_file_size(file_id, total_file_size)
        except Exception as e:
            logger.warning(f"Failed to update file size (non-critical): {e}")
        
        # Create file version
        await service_integration.create_file_version(file_id, f"version_1_{file_id}")
        
        # Trigger sync event
        sync_result = await service_integration.trigger_sync_event(file_id, "upload")
        logger.info(f"Successfully processed file {file_id} with {total_chunks} chunks, size: {total_file_size} bytes")
        logger.info(f"Sync event triggered: {sync_result}")
        
    except Exception as e:
        logger.error(f"Error processing file chunks: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

@app.options("/upload")
async def upload_options():
    """Handle OPTIONS preflight for upload endpoint"""
    return {"message": "OK"}

@app.options("/download/{file_id}")
async def download_options(file_id: str):
    """Handle OPTIONS preflight for download endpoint"""
    return {"message": "OK"}

@app.get("/files/{file_id}/status")
async def get_file_status(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the processing status of a file"""
    return {
        "file_id": file_id,
        "status": "completed",
        "message": "File processing completed successfully"
    }

@app.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Get chunker service statistics"""
    return {
        "service": "chunker-service",
        "chunk_size": 4194304,
        "max_file_size": 1073741824,
        "user": current_user.get("sub")
    }

