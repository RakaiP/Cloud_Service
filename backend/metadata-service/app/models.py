from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class File(Base):
    """SQLAlchemy model for file metadata"""
    __tablename__ = "files"

    # Use 'file_id' instead of 'id' to match the schema expectations
    file_id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_size = Column(Integer, default=0)  # NEW: Track actual file size
    owner_user_id = Column(String, nullable=False, index=True)  # ✅ ADD: Track file owner
    owner_email = Column(String, nullable=True, index=True)     # ✅ ADD: Track owner email
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with FileVersion - one file can have multiple versions
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")
    # Relationship with FileChunk - one file can have multiple chunks
    chunks = relationship("FileChunk", back_populates="file", cascade="all, delete-orphan")
    # Relationship with SharingPermission - one file can be shared with multiple users
    sharing_permissions = relationship("SharingPermission", back_populates="file", cascade="all, delete-orphan")

class FileVersion(Base):
    """SQLAlchemy model for file version tracking"""
    __tablename__ = "file_versions"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("files.file_id", ondelete="CASCADE"))
    version_number = Column(Integer)
    storage_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with File
    file = relationship("File", back_populates="versions")

class FileChunk(Base):
    """SQLAlchemy model for file chunks (for large files)"""
    __tablename__ = "file_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("files.file_id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    storage_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with File
    file = relationship("File", back_populates="chunks")

class SharingPermission(Base):
    """SQLAlchemy model for file sharing permissions"""
    __tablename__ = "sharing_permissions"

    id = Column(String, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("files.file_id", ondelete="CASCADE"))
    owner_user_id = Column(String, nullable=False)
    shared_with_user_id = Column(String, nullable=False)
    permissions = Column(String, default="read")  # "read" or "write"
    shared_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with File
    file = relationship("File", back_populates="sharing_permissions")