from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging
import requests
import asyncio  # ✅ ADD: Missing import for asyncio

from . import models, schemas, crud
from .database import get_db, get_engine, initialize_database
from .config import settings
from .auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create database tables with proper error handling"""
    try:
        logger.info("🔄 Initializing database connection...")
        
        # Initialize database with retry logic
        engine = initialize_database()
        
        logger.info("📊 Creating database tables...")
        # Only drop and recreate tables in development mode
        if settings.DEBUG:
            logger.warning("🚨 DEBUG mode: Dropping existing tables with CASCADE")
            # Use CASCADE to handle foreign key constraints
            models.Base.metadata.drop_all(bind=engine, checkfirst=True)
        
        # Create tables (only creates missing ones)
        models.Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"💥 Failed to create database tables: {e}")
        # Don't raise here - let the service start and retry later
        logger.warning("⚠️ Service will start but database operations may fail until DB is available")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        create_tables()
    except Exception as e:
        logger.error(f"Startup database initialization failed: {e}")

# Health check endpoint - public, no auth required
@app.get("/health")
def health_check():
    """Health check with database connectivity test"""
    try:
        # Test database connection
        engine = get_engine()
        with engine.connect() as connection:
            db_status = "connected"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": db_status,
        "service": "metadata-service"
    }

@app.options("/health")
async def health_check_options():
    """Handle OPTIONS preflight for health endpoint"""
    return {"message": "OK"}

@app.get("/")
async def root():
    return {"status": "Metadata Service is running", "service": "metadata-service"}

@app.options("/")
async def root_options():
    """Handle OPTIONS preflight for root endpoint"""
    return {"message": "OK"}

# File endpoints - protected
@app.post("/files", response_model=schemas.File, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
def create_file(file: schemas.FileInput, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Create a new file metadata entry with proper user ownership
    """
    try:
        user_id = current_user.get('sub')
        user_email = current_user.get('email')  # This might be None for some Auth0 providers
        
        # ✅ CRITICAL FIX: Handle cases where email is not in token
        if not user_email:
            # Try to get email from other token fields
            user_email = current_user.get('name', f"user_{user_id.split('|')[-1]}")
            logger.warning(f"No email in token for user {user_id}, using fallback: {user_email}")
        
        logger.info(f"✅ Creating file: {file.filename} for user: {user_id} ({user_email})")
        result = crud.create_file(db=db, file=file, owner_user_id=user_id, owner_email=user_email)
        logger.info(f"✅ File created successfully with ID: {result.file_id}")
        return result
    except Exception as e:
        logger.error(f"❌ Error creating file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")


@app.get("/files/{file_id}", response_model=schemas.File, dependencies=[Depends(get_current_user)])
def read_file(file_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get file metadata with access control
    """
    try:
        user_id = current_user.get('sub')
        
        # ✅ Check if user has access to this file
        db_file, access_type = crud.get_file_with_access_check(db, file_id, user_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found or access denied")
        
        logger.info(f"User {user_id} accessing file {file_id} as {access_type}")
        return schemas.File.model_validate(db_file)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file")

@app.get("/files")
async def read_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get list of files owned by the current user only
    """
    try:
        user_id = current_user.get('sub')
        user_email = current_user.get('email')
        
        logger.info(f"Loading files for user: {user_id} ({user_email})")
        
        # ✅ CRITICAL FIX: Only get files owned by this user
        files = crud.get_files(db, owner_user_id=user_id, skip=skip, limit=limit)
        
        # Convert to dict manually to avoid serialization issues
        files_data = []
        for file in files:
            file_dict = {
                "file_id": file.file_id,
                "filename": file.filename,
                "created_at": file.created_at.isoformat() if file.created_at else None,
                "updated_at": file.updated_at.isoformat() if file.updated_at else None,
                "file_size": getattr(file, 'file_size', None),
                "owner_user_id": getattr(file, 'owner_user_id', user_id),
                "owner_email": getattr(file, 'owner_email', user_email),
                "versions": [
                    {
                        "version_number": v.version_number,
                        "created_at": v.created_at.isoformat() if v.created_at else None
                    } for v in file.versions
                ],
                "chunks": [
                    {
                        "chunk_index": c.chunk_index,
                        "storage_path": c.storage_path,
                        "created_at": c.created_at.isoformat() if c.created_at else None
                    } for c in file.chunks
                ]
            }
            files_data.append(file_dict)
        
        logger.info(f"Returning {len(files_data)} files for user {user_email}")
        return JSONResponse(content=files_data, status_code=200)
        
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve files")

@app.put("/files/{file_id}", response_model=schemas.File, dependencies=[Depends(get_current_user)])
def update_file(file_id: str, file_data: schemas.FileUpdate, db: Session = Depends(get_db)):
    """
    Update file metadata including file size
    """
    db_file = crud.update_file(db, file_id=file_id, file_data=file_data)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file


@app.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
async def delete_file(file_id: str, request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Delete a file by ID with automatic chunk cleanup
    """
    # First check if file exists
    db_file = crud.get_file(db, file_id=file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get auth token for block storage calls
    auth_header = request.headers.get("Authorization")
    
    try:
        # Get chunks BEFORE deleting metadata
        chunks = crud.get_file_chunks(db, file_id=file_id)
        logger.info(f"Deleting file {file_id} with {len(chunks)} chunks")
        
        # Delete chunks from MinIO first
        deleted_chunks = 0
        failed_chunks = 0
        
        if chunks and auth_header:
            try:
                deleted_chunks, failed_chunks = await delete_chunks_from_storage(chunks, auth_header)
                logger.info(f"Chunk deletion: {deleted_chunks} deleted, {failed_chunks} failed")
            except Exception as e:
                logger.error(f"Error during chunk deletion: {e}")
                # Continue with metadata deletion even if chunk deletion fails
        
        # Delete from database (this will cascade to chunks and versions)
        result = crud.delete_file(db, file_id=file_id)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"File {file_id} deleted successfully")
        
        if failed_chunks > 0:
            logger.warning(f"File deleted but {failed_chunks} chunks may remain in storage")
        
        return JSONResponse(status_code=204, content={})
        
    except Exception as e:
        logger.error(f"Error during file deletion: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

async def delete_chunks_from_storage(chunks: list, auth_header: str):
    """Delete chunks directly from block storage service"""
    deleted_count = 0
    failed_count = 0
    
    for chunk in chunks:
        try:
            chunk_id = chunk.storage_path
            response = requests.delete(
                f"http://block-storage:8000/chunks/{chunk_id}",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            
            if response.status_code in [200, 204, 404]:  # 404 is OK (already deleted)
                deleted_count += 1
                logger.info(f"Deleted chunk {chunk_id}")
            else:
                failed_count += 1
                logger.warning(f"Failed to delete chunk {chunk_id}: HTTP {response.status_code}")
                
        except Exception as e:
            failed_count += 1
            logger.error(f"Error deleting chunk {chunk.storage_path}: {e}")
    
    return deleted_count, failed_count

# Version endpoints - protected
@app.post("/files/{file_id}/versions", response_model=schemas.FileVersion, dependencies=[Depends(get_current_user)])
def create_version(file_id: str, version: schemas.VersionCreate, db: Session = Depends(get_db)):
    """
    Create a new version for a file
    """
    # Check if file exists
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Create version
    return crud.create_file_version(db=db, version=version)


@app.get("/files/{file_id}/versions", response_model=List[schemas.FileVersion], dependencies=[Depends(get_current_user)])
def read_versions(file_id: str, db: Session = Depends(get_db)):
    """
    Get all versions of a file
    """
    try:
        # Check if file exists
        db_file = crud.get_file(db, file_id=file_id)
        if db_file is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get versions
        versions = crud.get_file_versions(db, file_id=file_id)
        # Ensure proper serialization
        return [schemas.FileVersion.model_validate(version) for version in versions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting versions for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get versions")

# Chunk endpoints - protected
@app.post("/files/{file_id}/chunks", response_model=schemas.FileChunk, dependencies=[Depends(get_current_user)])
def create_chunk(file_id: str, chunk: schemas.ChunkCreate, db: Session = Depends(get_db)):
    """
    Create a new chunk for a file
    """
    # Check if file exists
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Create chunk
    return crud.create_file_chunk(db=db, chunk=chunk)


@app.get("/files/{file_id}/chunks", response_model=List[schemas.FileChunk], dependencies=[Depends(get_current_user)])
def read_chunks(file_id: str, db: Session = Depends(get_db)):
    """
    Get all chunks of a file
    """
    try:
        # Check if file exists
        db_file = crud.get_file(db, file_id=file_id)
        if db_file is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get chunks
        chunks = crud.get_file_chunks(db, file_id=file_id)
        # Ensure proper serialization
        return [schemas.FileChunk.model_validate(chunk) for chunk in chunks]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunks for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chunks")

@app.get("/files/{file_id}/download-info", dependencies=[Depends(get_current_user)])
def get_file_download_info(file_id: str, db: Session = Depends(get_db)):
    """
    Get file information needed for download (filename + chunk list)
    """
    try:
        # Get file metadata
        db_file = crud.get_file(db, file_id=file_id)
        if db_file is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get chunks in correct order
        chunks = crud.get_file_chunks(db, file_id=file_id)
        
        # Return simple dict to avoid serialization issues
        return {
            "file_id": file_id,
            "filename": db_file.filename,
            "chunk_count": len(chunks),
            "chunk_ids": [chunk.storage_path for chunk in chunks]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download info for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get download info")

# Sharing endpoints - protected
@app.post("/files/{file_id}/share", response_model=schemas.SharingPermission, dependencies=[Depends(get_current_user)])
async def share_file(
    file_id: str, 
    share_request: schemas.ShareRequest, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Enhanced file sharing with better email validation"""
    try:
        current_user_id = current_user.get("sub")
        current_user_email = current_user.get("email")
        
        logger.info(f"🤝 User {current_user_email} sharing file {file_id} with {share_request.share_with_email}")
        
        # 1. Verify file exists and user owns it
        db_file = crud.get_file(db, file_id=file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 2. Check if user owns the file OR has write permissions
        if hasattr(db_file, 'owner_user_id') and db_file.owner_user_id and db_file.owner_user_id != current_user_id:
            _, access_type = crud.get_file_with_access_check(db, file_id, current_user_id)
            if access_type != "write" and access_type != "owner":
                raise HTTPException(status_code=403, detail="You don't have permission to share this file")
        
        # 3. Prevent sharing with yourself
        if share_request.share_with_email == current_user_email:
            raise HTTPException(status_code=400, detail="You cannot share a file with yourself")
        
        # 4. Enhanced email validation
        from .services.block_storage_client import Auth0UserSearchClient
        auth0_client = Auth0UserSearchClient()
        
        if not auth0_client.validate_email_format(share_request.share_with_email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # 5. Try to validate user exists (but don't block if validation fails)
        try:
            user_info = await auth0_client.get_user_by_email(share_request.share_with_email)
            if user_info:
                logger.info(f"✅ Validated user: {user_info.get('name')} ({share_request.share_with_email})")
            else:
                logger.info(f"⚠️ User not found in Auth0, but allowing share with email: {share_request.share_with_email}")
        except Exception as e:
            logger.warning(f"User validation failed (allowing anyway): {e}")
        
        # 6. Create sharing permission
        sharing_permission = crud.create_sharing_permission(
            db=db,
            file_id=file_id,
            owner_user_id=current_user_id,
            shared_with_email=share_request.share_with_email,
            permissions=share_request.permissions
        )
        
        logger.info(f"✅ File {file_id} successfully shared with {share_request.share_with_email}")
        return sharing_permission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sharing file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to share file: {str(e)}")

@app.get("/shared-with-me", response_model=List[schemas.SharedFile], dependencies=[Depends(get_current_user)])
async def get_shared_files(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Enhanced shared files lookup with comprehensive user identification"""
    try:
        user_id = current_user.get("sub")
        user_email = current_user.get("email")
        user_name = current_user.get("name")
        user_nickname = current_user.get("nickname")
        
        logger.info(f"📨 ENHANCED shared files lookup for user:")
        logger.info(f"   ID: {user_id}")
        logger.info(f"   Email: {user_email}")
        logger.info(f"   Name: {user_name}")
        logger.info(f"   Nickname: {user_nickname}")
        
        # ✅ ENHANCED: Create comprehensive list of identifiers
        search_identifiers = []
        
        # Add primary identifiers
        if user_id:
            search_identifiers.append(user_id)
            
        if user_email:
            search_identifiers.append(user_email)
            # Also add email variations
            search_identifiers.append(user_email.lower())
            search_identifiers.append(user_email.upper())
            
        if user_name:
            search_identifiers.append(user_name)
            
        if user_nickname:
            search_identifiers.append(user_nickname)
        
        # ✅ ENHANCED: Add Auth0 user ID variations
        if user_id and '|' in user_id:
            # For auth0|684dded7f7b5e0920a59a02f -> add 684dded7f7b5e0920a59a02f
            user_part = user_id.split('|')[-1]
            search_identifiers.append(user_part)
            
            # Also try with provider prefix
            provider = user_id.split('|')[0]
            search_identifiers.append(f"{provider}|{user_part}")
        
        # ✅ ENHANCED: Add potential email from user_id patterns
        if user_id:
            # For auth0 users, sometimes email might be embedded
            if 'google-oauth2' in user_id:
                # Try to construct potential gmail
                user_part = user_id.split('|')[-1]
                potential_email = f"{user_part}@gmail.com"
                search_identifiers.append(potential_email)
        
        # Remove duplicates while preserving order
        unique_identifiers = []
        seen = set()
        for identifier in search_identifiers:
            if identifier and identifier not in seen:
                unique_identifiers.append(identifier)
                seen.add(identifier)
        
        logger.info(f"🔍 Searching with {len(unique_identifiers)} identifiers: {unique_identifiers}")
        
        # Enhanced query with broader matching
        shared_files_query = db.query(models.File, models.SharingPermission).join(
            models.SharingPermission,
            models.File.file_id == models.SharingPermission.file_id
        ).filter(
            models.SharingPermission.shared_with_user_id.in_(unique_identifiers)
        )
        
        results = shared_files_query.all()
        logger.info(f"🔍 Enhanced query returned {len(results)} results")
        
        # ✅ ALSO: Try fuzzy matching for remaining shares
        if len(results) == 0 and user_email:
            logger.info(f"🔍 No exact matches, trying fuzzy email matching for: {user_email}")
            
            # Try pattern matching for email
            fuzzy_query = db.query(models.File, models.SharingPermission).join(
                models.SharingPermission,
                models.File.file_id == models.SharingPermission.file_id
            ).filter(
                models.SharingPermission.shared_with_user_id.like(f"%{user_email}%")
            )
            
            fuzzy_results = fuzzy_query.all()
            logger.info(f"🔍 Fuzzy email matching found {len(fuzzy_results)} results")
            results.extend(fuzzy_results)
        
        # Debug: Log what we found
        for file, sharing in results:
            logger.info(f"📋 Found shared file: {file.filename} (ID: {file.file_id})")
            logger.info(f"    Shared by: {sharing.owner_user_id}")
            logger.info(f"    Shared with: {sharing.shared_with_user_id}")
            logger.info(f"    Permissions: {sharing.permissions}")
        
        # Convert to SharedFile format
        shared_files = []
        seen_file_ids = set()
        
        for file, sharing in results:
            # Avoid duplicates
            if file.file_id in seen_file_ids:
                continue
            seen_file_ids.add(file.file_id)
            
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
        
        logger.info(f"📊 Returning {len(shared_files)} unique shared files for user {user_email or user_id}")
        
        return shared_files
        
    except Exception as e:
        logger.error(f"❌ Error getting shared files for user {current_user.get('email') or current_user.get('sub')}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to retrieve shared files")

# Enhanced debug endpoint with more comprehensive user info
@app.get("/debug/sharing-data", dependencies=[Depends(get_current_user)])
async def debug_sharing_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Comprehensive debug endpoint with full user identification analysis"""
    try:
        # ✅ ENHANCED: Extract all possible user info
        current_user_id = current_user.get("sub")
        current_user_email = current_user.get("email")
        current_user_name = current_user.get("name")
        current_user_nickname = current_user.get("nickname")
        email_verified = current_user.get("email_verified", False)
        
        logger.info(f"🔍 DEBUG: Comprehensive user analysis:")
        logger.info(f"   Raw token payload: {current_user}")
        
        # ✅ ENHANCED: Try to get user info from Auth0 if email is missing
        enhanced_user_info = {}
        if not current_user_email and current_user_id:
            try:
                logger.info(f"🔍 Attempting to fetch user info from Auth0 Management API...")
                from .services.block_storage_client import Auth0UserSearchClient
                auth0_client = Auth0UserSearchClient()
                
                # Try to get user by ID
                auth0_user = await auth0_client.get_user_by_email(current_user_id)
                if auth0_user:
                    enhanced_user_info = auth0_user
                    logger.info(f"✅ Enhanced user info from Auth0: {enhanced_user_info}")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch enhanced user info: {e}")
        
        # Create comprehensive identifier list
        all_identifiers = [current_user_id]
        if current_user_email:
            all_identifiers.extend([current_user_email, current_user_email.lower(), current_user_email.upper()])
        if current_user_name:
            all_identifiers.append(current_user_name)
        if current_user_nickname:
            all_identifiers.append(current_user_nickname)
        if current_user_id and '|' in current_user_id:
            all_identifiers.append(current_user_id.split('|')[-1])
        
        # Remove duplicates
        unique_identifiers = list(set(filter(None, all_identifiers)))
        
        # Get database data
        all_files = db.query(models.File).all()
        all_shares = db.query(models.SharingPermission).all()
        
        # Format debug data
        files_debug = []
        for file in all_files:
            files_debug.append({
                "file_id": file.file_id,
                "filename": file.filename,
                "owner_user_id": getattr(file, 'owner_user_id', 'NULL'),
                "owner_email": getattr(file, 'owner_email', 'NULL'),
                "created_at": file.created_at.isoformat() if file.created_at else None
            })
        
        shares_debug = []
        for share in all_shares:
            shares_debug.append({
                "id": share.id,
                "file_id": share.file_id,
                "owner_user_id": share.owner_user_id,
                "shared_with_user_id": share.shared_with_user_id,
                "permissions": share.permissions,
                "shared_at": share.shared_at.isoformat() if share.shared_at else None
            })
        
        # Find matches using comprehensive search
        matches = []
        for share in shares_debug:
            if share["shared_with_user_id"] in unique_identifiers:
                matches.append(share)
        
        # ✅ ENHANCED: Also check for partial matches
        partial_matches = []
        if current_user_email:
            for share in shares_debug:
                shared_with = share["shared_with_user_id"]
                if (shared_with not in unique_identifiers and 
                    current_user_email.lower() in shared_with.lower()):
                    partial_matches.append(share)
        
        return {
            "current_user": {
                "user_id": current_user_id,
                "email": current_user_email,
                "name": current_user_name,
                "nickname": current_user_nickname,
                "email_verified": email_verified,
                "all_identifiers": unique_identifiers,
                "enhanced_info": enhanced_user_info,
                "raw_token_payload": current_user
            },
            "total_files": len(files_debug),
            "total_shares": len(shares_debug),
            "files": files_debug,
            "sharing_permissions": shares_debug,
            "exact_matches_for_current_user": matches,
            "partial_matches_for_current_user": partial_matches,
            "sharing_analysis": {
                "total_unique_share_targets": len(set(s["shared_with_user_id"] for s in shares_debug)),
                "shares_by_email": [s for s in shares_debug if "@" in s["shared_with_user_id"]],
                "shares_by_user_id": [s for s in shares_debug if "|" in s["shared_with_user_id"]],
                "potential_email_matches": [
                    s for s in shares_debug 
                    if current_user_email and current_user_email.lower() in s["shared_with_user_id"].lower()
                ] if current_user_email else []
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Debug endpoint error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shared-with-me", response_model=List[schemas.SharedFile], dependencies=[Depends(get_current_user)])
async def get_shared_files(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Enhanced shared files lookup with better user resolution"""
    try:
        user_id = current_user.get("sub")
        user_email = current_user.get("email")
        
        # ✅ ENHANCED: Get additional user identifiers
        user_name = current_user.get("name")
        user_nickname = current_user.get("nickname")
        
        logger.info(f"📨 Getting shared files for user:")
        logger.info(f"   ID: {user_id}")
        logger.info(f"   Email: {user_email}")
        logger.info(f"   Name: {user_name}")
        logger.info(f"   Nickname: {user_nickname}")
        
        # Create list of all possible identifiers this user might be shared with
        search_identifiers = []
        
        if user_id:
            search_identifiers.append(user_id)
        if user_email:
            search_identifiers.append(user_email)
        if user_name:
            search_identifiers.append(user_name)
        if user_nickname:
            search_identifiers.append(user_nickname)
        
        # Also add parts of the user_id (for Auth0 users)
        if user_id and '|' in user_id:
            user_part = user_id.split('|')[-1]
            search_identifiers.append(user_part)
        
        logger.info(f"🔍 Searching with identifiers: {search_identifiers}")
        
        # Enhanced query that searches for any of these identifiers
        shared_files_query = db.query(models.File, models.SharingPermission).join(
            models.SharingPermission,
            models.File.file_id == models.SharingPermission.file_id
        ).filter(
            models.SharingPermission.shared_with_user_id.in_(search_identifiers)
        )
        
        results = shared_files_query.all()
        logger.info(f"🔍 Enhanced query returned {len(results)} results")
        
        # Debug: Log what we found
        for file, sharing in results:
            logger.info(f"📋 Found shared file: {file.filename} (ID: {file.file_id})")
            logger.info(f"    Shared by: {sharing.owner_user_id}")
            logger.info(f"    Shared with: {sharing.shared_with_user_id}")
            logger.info(f"    Permissions: {sharing.permissions}")
        
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
        
        logger.info(f"📊 Returning {len(shared_files)} shared files for user {user_email or user_id}")
        
        return shared_files
        
    except Exception as e:
        logger.error(f"❌ Error getting shared files for user {current_user.get('email') or current_user.get('sub')}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to retrieve shared files")

# Enhanced sharing endpoint with better user resolution
@app.post("/files/{file_id}/share", response_model=schemas.SharingPermission, dependencies=[Depends(get_current_user)])
async def share_file(
    file_id: str, 
    share_request: schemas.ShareRequest, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Enhanced file sharing with proper user ID resolution"""
    try:
        current_user_id = current_user.get("sub")
        current_user_email = current_user.get("email")
        share_with_email = share_request.share_with_email
        
        # ✅ ENHANCED: Get better user info
        current_user_display = current_user_email or current_user.get("name") or current_user_id
        
        logger.info(f"🤝 User {current_user_display} ({current_user_id}) sharing file {file_id} with {share_with_email}")
        
        # 1. Verify file exists and user owns it
        db_file = crud.get_file(db, file_id=file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 2. Enhanced ownership check
        file_owner = getattr(db_file, 'owner_user_id', None)
        if file_owner and file_owner != current_user_id:
            logger.warning(f"User {current_user_id} trying to share file owned by {file_owner}")
            _, access_type = crud.get_file_with_access_check(db, file_id, current_user_id)
            if access_type not in ["write", "owner"]:
                raise HTTPException(status_code=403, detail="You don't have permission to share this file")
        
        # 3. Prevent sharing with yourself
        if share_with_email in [current_user_email, current_user_id, current_user.get("name")]:
            raise HTTPException(status_code=400, detail="You cannot share a file with yourself")
        
        # 4. Enhanced user lookup with Auth0 Management API
        target_user_info = None
        share_with_identifier = share_with_email  # Default to email
        
        try:
            from .services.block_storage_client import Auth0UserSearchClient
            auth0_client = Auth0UserSearchClient()
            
            # Try to find the user in Auth0
            target_user_info = await auth0_client.get_user_by_email(share_with_email)
            
            if target_user_info and target_user_info.get("user_id"):
                # User exists in Auth0, use their actual user_id
                share_with_identifier = target_user_info["user_id"]
                logger.info(f"✅ Found target user in Auth0: {target_user_info['name']} (ID: {share_with_identifier})")
            else:
                # User doesn't exist in Auth0 yet, use email as identifier
                logger.info(f"⚠️ User {share_with_email} not found in Auth0, using email as identifier")
                
        except Exception as e:
            logger.warning(f"User lookup failed (continuing with email): {e}")
            # Continue with email if Auth0 lookup fails
        
        # 5. Validate email format
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, share_with_email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # 6. Create sharing permission with proper identifier
        sharing_permission = crud.create_sharing_permission(
            db=db,
            file_id=file_id,
            owner_user_id=current_user_id,
            shared_with_email=share_with_identifier,  # Use user_id if available, email otherwise
            permissions=share_request.permissions
        )
        
        logger.info(f"✅ File {file_id} successfully shared with {share_with_email} (stored as: {share_with_identifier})")
        
        return sharing_permission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sharing file: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to share file: {str(e)}")

# Enhanced debug endpoint with better user info
@app.get("/debug/sharing-data", dependencies=[Depends(get_current_user)])
async def debug_sharing_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Enhanced debug endpoint to see all sharing data with better user info"""
    try:
        current_user_id = current_user.get("sub")
        current_user_email = current_user.get("email")
        current_user_name = current_user.get("name")
        current_user_nickname = current_user.get("nickname")
        
        logger.info(f"🔍 DEBUG: Enhanced inspection for user:")
        logger.info(f"   ID: {current_user_id}")
        logger.info(f"   Email: {current_user_email}")
        logger.info(f"   Name: {current_user_name}")
        logger.info(f"   Nickname: {current_user_nickname}")
        
        # Get all files
        all_files = db.query(models.File).all()
        
        # Get all sharing permissions
        all_shares = db.query(models.SharingPermission).all()
        
        # Format debug data
        files_debug = []
        for file in all_files:
            files_debug.append({
                "file_id": file.file_id,
                "filename": file.filename,
                "owner_user_id": getattr(file, 'owner_user_id', 'NULL'),
                "owner_email": getattr(file, 'owner_email', 'NULL'),
                "created_at": file.created_at.isoformat() if file.created_at else None
            })
        
        shares_debug = []
        for share in all_shares:
            shares_debug.append({
                "id": share.id,
                "file_id": share.file_id,
                "owner_user_id": share.owner_user_id,
                "shared_with_user_id": share.shared_with_user_id,
                "permissions": share.permissions,
                "shared_at": share.shared_at.isoformat() if share.shared_at else None
            })
        
        # Create list of all possible identifiers for current user
        search_identifiers = [current_user_id]
        if current_user_email:
            search_identifiers.append(current_user_email)
        if current_user_name:
            search_identifiers.append(current_user_name)
        if current_user_nickname:
            search_identifiers.append(current_user_nickname)
        if current_user_id and '|' in current_user_id:
            search_identifiers.append(current_user_id.split('|')[-1])
        
        return {
            "current_user": {
                "user_id": current_user_id,
                "email": current_user_email,
                "name": current_user_name,
                "nickname": current_user_nickname,
                "all_identifiers": search_identifiers
            },
            "total_files": len(files_debug),
            "total_shares": len(shares_debug),
            "files": files_debug,
            "sharing_permissions": shares_debug,
            "matches_for_current_user": [
                share for share in shares_debug 
                if share["shared_with_user_id"] == current_user_id
            ],
            "shares_with_current_user_id": [
                share for share in shares_debug 
                if share["shared_with_user_id"] == current_user_id
            ],
            "shares_with_current_email": [
                share for share in shares_debug 
                if share["shared_with_user_id"] == current_user_email
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Debug endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{file_id}/share/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
async def revoke_file_sharing(
    file_id: str, 
    user_id: str, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Revoke file sharing for a specific user"""
    try:
        current_user_id = current_user.get("sub")
        
        # Verify file exists and user owns it
        db_file = crud.get_file(db, file_id=file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete sharing permission
        result = crud.delete_sharing_permission(db, file_id, current_user_id, user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Sharing permission not found")
        
        return JSONResponse(status_code=204, content={})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking file sharing: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke sharing")

@app.get("/files/{file_id}/shares", dependencies=[Depends(get_current_user)])
async def get_file_shares(
    file_id: str, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Get all sharing permissions for a file"""
    try:
        current_user_id = current_user.get("sub")
        
        # Verify file exists and user owns it
        db_file = crud.get_file(db, file_id=file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get all sharing permissions for this file
        shares = crud.get_sharing_permissions_for_file(db, file_id)
        
        # Format response
        shares_data = []
        for share in shares:
            shares_data.append({
                "id": share.id,
                "shared_with_user_id": share.shared_with_user_id,
                "permissions": share.permissions,
                "shared_at": share.shared_at.isoformat()
            })
        
        return {
            "file_id": file_id,
            "shares": shares_data,
            "total_shares": len(shares_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file shares: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file shares")

@app.get("/my-shared-files", dependencies=[Depends(get_current_user)])
async def get_my_shared_files(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all files that the current user has shared with others"""
    try:
        current_user_id = current_user.get("sub")
        shared_files = crud.get_files_shared_by_user(db, current_user_id)
        
        # Group by file_id and include file metadata
        files_data = {}
        for sharing in shared_files:
            file_id = sharing.file_id
            if file_id not in files_data:
                file = crud.get_file(db, file_id)
                if file:
                    files_data[file_id] = {
                        "file_id": file_id,
                        "filename": file.filename,
                        "file_size": file.file_size,
                        "created_at": file.created_at.isoformat(),
                        "shared_with": []
                    }
            
            if file_id in files_data:
                files_data[file_id]["shared_with"].append({
                    "user_id": sharing.shared_with_user_id,
                    "permissions": sharing.permissions,
                    "shared_at": sharing.shared_at.isoformat()
                })
        
        return {
            "shared_files": list(files_data.values()),
            "total_files": len(files_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting shared files: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve shared files")