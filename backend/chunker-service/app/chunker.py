import hashlib
import os
from typing import List, Tuple, AsyncGenerator
from fastapi import UploadFile
import aiofiles

class FileChunker:
    """Handles file chunking operations"""
    
    def __init__(self, chunk_size: int = 1024 * 1024):  # 1MB default
        self.chunk_size = chunk_size
    
    async def chunk_file(self, file: UploadFile, user_id: str) -> AsyncGenerator[Tuple[int, bytes, str], None]:
        """
        Chunk a file into smaller pieces
        
        Args:
            file: The uploaded file
            user_id: ID of the user uploading the file
            
        Yields:
            Tuple of (chunk_index, chunk_data, chunk_hash)
        """
        chunk_index = 0
        
        # Reset file pointer to beginning
        await file.seek(0)
        
        while True:
            # Read chunk data
            chunk_data = await file.read(self.chunk_size)
            
            if not chunk_data:
                break
            
            # Calculate chunk hash for integrity
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            
            yield chunk_index, chunk_data, chunk_hash
            chunk_index += 1
    
    def calculate_file_hash(self, chunks_data: List[bytes]) -> str:
        """Calculate hash of entire file from chunks"""
        hasher = hashlib.sha256()
        for chunk_data in chunks_data:
            hasher.update(chunk_data)
        return hasher.hexdigest()
    
    async def get_file_info(self, file: UploadFile) -> dict:
        """Get basic file information"""
        # Get file size by seeking to end and getting position
        await file.seek(0)  # Start at beginning
        
        # Read all content to get size (since UploadFile doesn't support seek with offset)
        content = await file.read()
        file_size = len(content)
        
        # Reset file pointer to beginning for subsequent operations
        await file.seek(0)
        
        # Calculate number of chunks
        num_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
        
        return {
            "filename": file.filename,
            "size": file_size,
            "content_type": file.content_type,
            "num_chunks": num_chunks,
            "chunk_size": self.chunk_size
        }
