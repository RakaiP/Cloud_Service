from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# File schemas
class FileBase(BaseModel):
    """Base schema with common file attributes"""
    filename: str


class FileInput(FileBase):
    """Schema for file creation input"""
    pass


class FileVersion(BaseModel):
    """Schema for file version"""
    version_number: int
    created_at: datetime
    
    class Config:
        orm_mode = True


class FileChunk(BaseModel):
    """Schema for file chunk"""
    chunk_index: int
    storage_path: str
    created_at: datetime
    
    class Config:
        orm_mode = True


class File(FileBase):
    """Schema for file response"""
    file_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    versions: List[FileVersion] = []
    chunks: List[FileChunk] = []
    
    class Config:
        orm_mode = True


# Version schemas
class VersionCreate(BaseModel):
    """Schema for creating a new version"""
    file_id: str
    storage_path: str


# Chunk schemas
class ChunkCreate(BaseModel):
    """Schema for creating a new chunk"""
    file_id: str
    chunk_index: int
    storage_path: str