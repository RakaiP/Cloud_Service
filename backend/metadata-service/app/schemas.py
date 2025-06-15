from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional

# File schemas
class FileBase(BaseModel):
    """Base schema with common file attributes"""
    filename: str


class FileInput(FileBase):
    """Schema for file creation input"""
    pass


class FileUpdate(BaseModel):
    """Schema for file updates"""
    filename: Optional[str] = None
    file_size: Optional[int] = None


class FileVersion(BaseModel):
    """Schema for file version"""
    version_number: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FileChunk(BaseModel):
    """Schema for file chunk"""
    chunk_index: int
    storage_path: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class File(FileBase):
    """Schema for file response"""
    file_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    file_size: Optional[int] = None
    versions: List[FileVersion] = []
    chunks: List[FileChunk] = []
    
    model_config = ConfigDict(
        from_attributes=True,
        # Prevent recursion issues - updated for Pydantic V2
        str_max_length=10000,  # Updated from max_anystr_length
        validate_assignment=True
    )


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


# Sharing schemas
class ShareRequest(BaseModel):
    """Schema for sharing a file with another user"""
    share_with_email: str
    permissions: str = Field(default="read", pattern="^(read|write)$")


class SharingPermission(BaseModel):
    """Schema for sharing permission response"""
    id: str
    file_id: str
    owner_user_id: str
    shared_with_user_id: str
    permissions: str
    shared_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SharedFile(BaseModel):
    """Schema for files shared with user"""
    file_id: str
    filename: str
    owner_user_id: str
    permissions: str
    shared_at: datetime
    file_size: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)