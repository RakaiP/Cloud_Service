from sqlalchemy.orm import Session
import uuid
from . import models, schemas

def get_file(db: Session, file_id: str):
    """
    Get a file by ID
    """
    return db.query(models.File).filter(models.File.id == file_id).first()


def get_files(db: Session, skip: int = 0, limit: int = 100):
    """
    Get multiple files with pagination
    """
    return db.query(models.File).offset(skip).limit(limit).all()


def create_file(db: Session, file: schemas.FileInput):
    """
    Create a new file record
    """
    file_id = str(uuid.uuid4())
    db_file = models.File(id=file_id, filename=file.filename)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def delete_file(db: Session, file_id: str):
    """
    Delete a file by ID
    """
    db_file = get_file(db, file_id)
    if db_file:
        db.delete(db_file)
        db.commit()
        return True
    return False


def update_file(db: Session, file_id: str, file_data: schemas.FileInput):
    """
    Update a file's metadata
    """
    db_file = get_file(db, file_id)
    if db_file:
        for key, value in file_data.dict().items():
            setattr(db_file, key, value)
        db.commit()
        db.refresh(db_file)
        return db_file
    return None


def create_file_version(db: Session, version: schemas.VersionCreate):
    """
    Create a new file version
    """
    # Find the highest version number for this file
    highest_version = db.query(models.FileVersion).filter(
        models.FileVersion.file_id == version.file_id
    ).order_by(models.FileVersion.version_number.desc()).first()
    
    # Set version number to 1 if no versions exist, otherwise increment
    new_version_number = 1 if not highest_version else highest_version.version_number + 1
    
    # Create new version
    db_version = models.FileVersion(
        file_id=version.file_id,
        version_number=new_version_number,
        storage_path=version.storage_path
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


def create_file_chunk(db: Session, chunk: schemas.ChunkCreate):
    """
    Create a new file chunk
    """
    db_chunk = models.FileChunk(
        file_id=chunk.file_id,
        chunk_index=chunk.chunk_index,
        storage_path=chunk.storage_path
    )
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk


def get_file_versions(db: Session, file_id: str):
    """
    Get all versions of a file
    """
    return db.query(models.FileVersion).filter(
        models.FileVersion.file_id == file_id
    ).order_by(models.FileVersion.version_number).all()


def get_file_chunks(db: Session, file_id: str):
    """
    Get all chunks of a file
    """
    return db.query(models.FileChunk).filter(
        models.FileChunk.file_id == file_id
    ).order_by(models.FileChunk.chunk_index).all()