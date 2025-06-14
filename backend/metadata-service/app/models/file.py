from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(String, ForeignKey("users.id"))

    # Relationships
    owner = relationship("User", back_populates="files")
    chunks = relationship("FileChunk", back_populates="file", cascade="all, delete-orphan")
    total_chunks = Column(Integer, default=0)
    upload_status = Column(String, default="pending")  # pending, uploading, completed, failed

class FileChunk(Base):
    __tablename__ = "file_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=False)
    chunk_id = Column(String, unique=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)
    hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to file
    file = relationship("File", back_populates="chunks")