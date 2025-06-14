import os
import aiofiles
from fastapi import UploadFile

STORAGE_DIR = "storage"

async def save_chunk_to_disk(chunk_id: str, file: UploadFile) -> str:
    """Save chunk file to local disk storage"""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    storage_path = os.path.join(STORAGE_DIR, f"{chunk_id}.chunk")
    
    async with aiofiles.open(storage_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return storage_path

def get_chunk_filepath(chunk_id: str) -> str:
    """Get full filepath for a chunk"""
    return os.path.join(STORAGE_DIR, f"{chunk_id}.chunk")

def delete_chunk_from_disk(chunk_path: str) -> None:
    """Delete chunk file from local disk"""
    os.remove(chunk_path)
