from sqlalchemy.orm import Session
import uuid
import logging  # ✅ ADD: Missing import for logging
from . import models, schemas

# ✅ ADD: Create logger instance
logger = logging.getLogger(__name__)

def get_file(db: Session, file_id: str):
    """
    Get a file by ID
    """
    return db.query(models.File).filter(models.File.file_id == file_id).first()


def get_files(db: Session, owner_user_id: str, skip: int = 0, limit: int = 100):
    """
    Get files owned by a specific user only
    """
    return db.query(models.File).filter(
        models.File.owner_user_id == owner_user_id
    ).offset(skip).limit(limit).all()


def create_file(db: Session, file: schemas.FileInput, owner_user_id: str, owner_email: str = None):
    """
    Create a new file record with enhanced user ownership handling
    """
    file_id = str(uuid.uuid4())
    
    # ✅ ENHANCED: Handle cases where owner_email might be None
    if not owner_email:
        # Create a fallback email from user_id
        if '|' in owner_user_id:
            # For Auth0 users like "google-oauth2|112121276812139100082"
            provider, user_part = owner_user_id.split('|', 1)
            owner_email = f"{user_part}@{provider}.auth0.local"
        else:
            owner_email = f"{owner_user_id}@unknown.local"
        
        logger.info(f"No email provided, using fallback: {owner_email}")
    
    db_file = models.File(
        file_id=file_id, 
        filename=file.filename,
        owner_user_id=owner_user_id,
        owner_email=owner_email
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    logger.info(f"✅ Created file {file_id} for user {owner_user_id} ({owner_email})")
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


def update_file(db: Session, file_id: str, file_data):
    """
    Update a file's metadata including file size
    """
    db_file = get_file(db, file_id)
    if db_file:
        # Handle both FileInput and FileUpdate schemas
        update_data = file_data.dict(exclude_unset=True) if hasattr(file_data, 'dict') else file_data
        
        for key, value in update_data.items():
            if value is not None:  # Only update non-None values
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


def get_file_with_access_check(db: Session, file_id: str, user_id: str):
    """Enhanced file access check with better user matching"""
    # First check if user owns the file
    db_file = db.query(models.File).filter(
        models.File.file_id == file_id,
        models.File.owner_user_id == user_id
    ).first()
    
    if db_file:
        return db_file, "owner"
    
    # Enhanced sharing check: Check by both user_id AND email patterns
    # Get user email from Auth0 if we have the user_id
    user_email = None
    
    # Check if file is shared with user (by user_id or email patterns)
    shared_access = db.query(models.File, models.SharingPermission).join(
        models.SharingPermission,
        models.File.file_id == models.SharingPermission.file_id
    ).filter(
        models.File.file_id == file_id,
        (
            # Check exact user_id match
            (models.SharingPermission.shared_with_user_id == user_id) |
            # Check if sharing was done by email pattern (for Auth0 users)
            (models.SharingPermission.shared_with_user_id.like(f"%{user_id.split('|')[-1]}%") if '|' in user_id else False)
        )
    ).first()
    
    if shared_access:
        return shared_access[0], shared_access[1].permissions
    
    return None, None

def create_sharing_permission(db: Session, file_id: str, owner_user_id: str, shared_with_email: str, permissions: str):
    """Enhanced sharing permission creation with better user resolution"""
    import uuid
    
    logger.info(f"Creating sharing permission: file={file_id}, owner={owner_user_id}, target={shared_with_email}")
    
    # Check if sharing permission already exists
    existing_share = db.query(models.SharingPermission).filter(
        models.SharingPermission.file_id == file_id,
        models.SharingPermission.shared_with_user_id == shared_with_email
    ).first()
    
    if existing_share:
        # Update existing permission
        logger.info(f"Updating existing sharing permission for {shared_with_email}")
        existing_share.permissions = permissions
        db.commit()
        db.refresh(existing_share)
        return existing_share
    
    # Create new sharing permission
    sharing_id = str(uuid.uuid4())
    db_sharing = models.SharingPermission(
        id=sharing_id,
        file_id=file_id,
        owner_user_id=owner_user_id,
        shared_with_user_id=shared_with_email,  # This could be user_id or email
        permissions=permissions
    )
    db.add(db_sharing)
    db.commit()
    db.refresh(db_sharing)
    
    logger.info(f"✅ Created sharing permission: {sharing_id}")
    return db_sharing

def get_files_shared_with_user(db: Session, user_identifier: str):
    """Enhanced shared files lookup with multiple identifier matching"""
    logger.info(f"🔍 Looking for files shared with identifier: {user_identifier}")
    
    # Enhanced query that handles different identifier formats
    results = db.query(models.File, models.SharingPermission).join(
        models.SharingPermission,
        models.File.file_id == models.SharingPermission.file_id
    ).filter(
        # Direct match
        models.SharingPermission.shared_with_user_id == user_identifier
    ).all()
    
    logger.info(f"🔍 Direct match found {len(results)} results for {user_identifier}")
    
    # If user_identifier is an Auth0 user_id, also check for email-based shares
    if '|' in user_identifier:
        # Extract potential email part from Auth0 user_id
        user_part = user_identifier.split('|')[-1]
        
        # Also search for shares that might have been created with email
        email_results = db.query(models.File, models.SharingPermission).join(
            models.SharingPermission,
            models.File.file_id == models.SharingPermission.file_id
        ).filter(
            models.SharingPermission.shared_with_user_id.like(f"%{user_part}%")
        ).all()
        
        logger.info(f"🔍 Email pattern match found {len(email_results)} results for {user_part}")
        
        # Combine results and deduplicate
        all_results = results + email_results
        seen_file_ids = set()
        unique_results = []
        
        for result in all_results:
            file_id = result[0].file_id
            if file_id not in seen_file_ids:
                unique_results.append(result)
                seen_file_ids.add(file_id)
        
        results = unique_results
    
    # Convert to SharedFile format
    shared_files = []
    for file, sharing in results:
        shared_file = {
            "file_id": file.file_id,
            "filename": file.filename,
            "owner_user_id": sharing.owner_user_id,
            "permissions": sharing.permissions,
            "shared_at": sharing.shared_at,
            "file_size": getattr(file, 'file_size', 0) or 0,
            "created_at": file.created_at
        }
        shared_files.append(shared_file)
        
        logger.info(f"📋 Shared file found: {file.filename} (shared by: {sharing.owner_user_id})")
    
    logger.info(f"📊 Total shared files for {user_identifier}: {len(shared_files)}")
    return shared_files


def delete_sharing_permission(db: Session, file_id: str, owner_user_id: str, shared_with_user_id: str):
    """Delete a sharing permission"""
    db_sharing = db.query(models.SharingPermission).filter(
        models.SharingPermission.file_id == file_id,
        models.SharingPermission.owner_user_id == owner_user_id,
        models.SharingPermission.shared_with_user_id == shared_with_user_id
    ).first()
    
    if db_sharing:
        db.delete(db_sharing)
        db.commit()
        return True
    return False


def get_sharing_permissions_for_file(db: Session, file_id: str):
    """Get all sharing permissions for a specific file"""
    return db.query(models.SharingPermission).filter(
        models.SharingPermission.file_id == file_id
    ).all()


def get_user_sharing_permission(db: Session, file_id: str, user_id: str):
    """Get sharing permission for a specific user and file"""
    return db.query(models.SharingPermission).filter(
        models.SharingPermission.file_id == file_id,
        models.SharingPermission.shared_with_user_id == user_id
    ).first()


def update_sharing_permission(db: Session, file_id: str, user_id: str, permissions: str):
    """Update sharing permissions for a user"""
    db_sharing = get_user_sharing_permission(db, file_id, user_id)
    if db_sharing:
        db_sharing.permissions = permissions
        db.commit()
        db.refresh(db_sharing)
        return db_sharing
    return None


def get_files_shared_by_user(db: Session, owner_user_id: str):
    """Get all files shared by a specific user"""
    return db.query(models.SharingPermission).filter(
        models.SharingPermission.owner_user_id == owner_user_id
    ).all()


def check_file_access(db: Session, file_id: str, user_id: str):
    """Check if user has access to a file (owner or shared)"""
    # Check if user owns the file (simplified - in production you'd have owner field)
    file = get_file(db, file_id)
    if not file:
        return False, None
    
    # Check if file is shared with user
    sharing = get_user_sharing_permission(db, file_id, user_id)
    if sharing:
        return True, sharing.permissions
    
    # For now, assume user owns file if no sharing found
    # TODO: Add proper ownership check when owner field is added
    return True, "write"


def get_file_sharing_stats(db: Session, file_id: str):
    """Get sharing statistics for a file"""
    sharing_count = db.query(models.SharingPermission).filter(
        models.SharingPermission.file_id == file_id
    ).count()
    
    permissions_breakdown = db.query(
        models.SharingPermission.permissions,
        db.func.count(models.SharingPermission.id)
    ).filter(
        models.SharingPermission.file_id == file_id
    ).group_by(models.SharingPermission.permissions).all()
    
    return {
        "total_shares": sharing_count,
        "permissions_breakdown": dict(permissions_breakdown)
    }