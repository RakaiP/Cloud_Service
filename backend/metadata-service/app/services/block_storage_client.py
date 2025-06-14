import requests
import hashlib
import os
from typing import List, Dict, Any
from io import BytesIO

class BlockStorageClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("BLOCK_STORAGE_URL", "http://block-storage:8000")
    
    def upload_chunk(self, chunk_data: bytes, chunk_id: str) -> Dict[str, Any]:
        """Upload a chunk to block storage"""
        files = {"file": BytesIO(chunk_data)}
        data = {"chunk_id": chunk_id}
        
        response = requests.post(f"{self.base_url}/chunks", files=files, data=data)
        response.raise_for_status()
        return response.json()
    
    def download_chunk(self, chunk_id: str) -> bytes:
        """Download a chunk from block storage"""
        response = requests.get(f"{self.base_url}/chunks/{chunk_id}")
        response.raise_for_status()
        return response.content
    
    def delete_chunk(self, chunk_id: str) -> Dict[str, Any]:
        """Delete a chunk from block storage"""
        response = requests.delete(f"{self.base_url}/chunks/{chunk_id}")
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if block storage is healthy"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

class FileChunker:
    def __init__(self, chunk_size: int = 1024 * 1024):  # 1MB chunks
        self.chunk_size = chunk_size
    
    def chunk_file(self, file_data: bytes, file_id: str) -> List[Dict[str, Any]]:
        """Split file into chunks and return chunk metadata"""
        chunks = []
        total_size = len(file_data)
        
        for i in range(0, total_size, self.chunk_size):
            chunk_data = file_data[i:i + self.chunk_size]
            chunk_index = i // self.chunk_size
            
            # Generate chunk ID and hash
            chunk_id = f"{file_id}_chunk_{chunk_index:04d}"
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            
            chunks.append({
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "size": len(chunk_data),
                "hash": chunk_hash,
                "data": chunk_data
            })
        
        return chunks
    
    def reconstruct_file(self, chunks: List[bytes]) -> bytes:
        """Reconstruct file from ordered chunks"""
        return b''.join(chunks)
