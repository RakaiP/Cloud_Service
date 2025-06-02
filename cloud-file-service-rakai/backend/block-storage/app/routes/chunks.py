from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import FileResponse
import os
import uuid
from app.utils import save_chunk_to_disk, get_chunk_filepath, delete_chunk_from_disk

router = APIRouter()

@router.post("/", status_code=201)
async def upload_chunk(
    file_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload a file chunk to local storage"""
    try:
        # Generate unique chunk ID with file_id, chunk_index, and random suffix
        chunk_id = f"{file_id}_{chunk_index}_{uuid.uuid4().hex[:8]}"
        
        # Save chunk to local disk storage
        storage_path = await save_chunk_to_disk(chunk_id, file)
        
        return {
            "chunk_id": chunk_id,
            "storage_path": storage_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload chunk: {str(e)}")

@router.get("/{chunk_id}")
async def download_chunk(chunk_id: str):
    """Download a file chunk by ID"""
    chunk_path = get_chunk_filepath(chunk_id)
    
    if not os.path.exists(chunk_path):
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    return FileResponse(
        path=chunk_path,
        media_type="application/octet-stream",
        filename=f"{chunk_id}.chunk"
    )

@router.delete("/{chunk_id}", status_code=204)
async def delete_chunk(chunk_id: str):
    """Delete a chunk by ID"""
    chunk_path = get_chunk_filepath(chunk_id)
    
    if not os.path.exists(chunk_path):
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    try:
        delete_chunk_from_disk(chunk_path)
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chunk: {str(e)}")
