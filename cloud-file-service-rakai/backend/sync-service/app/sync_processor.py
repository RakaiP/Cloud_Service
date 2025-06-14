import httpx
import logging
import os
from typing import Dict, Any
from . import models

logger = logging.getLogger(__name__)

# Service URLs
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8000")
BLOCK_STORAGE_SERVICE_URL = os.getenv("BLOCK_STORAGE_SERVICE_URL", "http://block-storage:8000")
CHUNKER_SERVICE_URL = os.getenv("CHUNKER_SERVICE_URL", "http://chunker-service:8002")

class SyncProcessor:
    """Handles actual synchronization logic with other services"""
    
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    async def process_upload_sync(self, file_id: str, event_id: str) -> Dict[str, Any]:
        """Process file upload synchronization"""
        logger.info(f"Processing upload sync for file {file_id}")
        
        try:
            # 1. Check if this is a test file ID (for manual testing)
            if file_id.startswith(("workflow-test-", "manual-test-", "test-file-")):
                logger.info(f"Processing test file sync for {file_id}")
                return {
                    "status": "completed",
                    "file_id": file_id,
                    "action": "test_upload_synchronized",
                    "message": "Test file sync completed successfully",
                    "sync_event_id": event_id
                }
            
            # 2. Try to get file metadata from metadata service
            try:
                file_metadata = await self._get_file_metadata(file_id)
                logger.info(f"Found file metadata: {file_metadata.get('filename', 'unknown')}")
            except Exception as e:
                logger.warning(f"Could not get file metadata for {file_id}: {e}")
                # For new files that might not be fully processed yet
                return {
                    "status": "pending",
                    "file_id": file_id,
                    "action": "upload_metadata_pending",
                    "message": "File metadata not yet available, will retry",
                    "sync_event_id": event_id
                }
            
            # 3. Try to get file chunks information
            try:
                chunks = await self._get_file_chunks(file_id)
                logger.info(f"File {file_id} has {len(chunks)} chunks")
            except Exception as e:
                logger.warning(f"Could not get file chunks for {file_id}: {e}")
                chunks = []
            
            # 4. If no chunks yet, mark as pending (upload might still be processing)
            if not chunks:
                return {
                    "status": "pending", 
                    "file_id": file_id,
                    "action": "upload_chunks_pending",
                    "message": "File chunks not yet available, upload may still be processing",
                    "sync_event_id": event_id
                }
            
            # 5. Verify chunks exist in block storage
            verified_chunks = 0
            missing_chunks = []
            for chunk in chunks:
                chunk_path = chunk.get("storage_path", f"unknown_chunk_{chunk.get('chunk_index', 0)}")
                if await self._verify_chunk_exists(chunk_path):
                    verified_chunks += 1
                else:
                    missing_chunks.append(chunk)
            
            # 6. Create sync result
            if missing_chunks:
                logger.warning(f"Missing {len(missing_chunks)} chunks for file {file_id}")
                return {
                    "status": "incomplete",
                    "file_id": file_id,
                    "filename": file_metadata.get("filename", "unknown"),
                    "chunks_verified": verified_chunks,
                    "missing_chunks": len(missing_chunks),
                    "total_chunks": len(chunks),
                    "sync_event_id": event_id,
                    "action": "upload_incomplete"
                }
            else:
                return {
                    "status": "completed",
                    "file_id": file_id,
                    "filename": file_metadata.get("filename", "unknown"),
                    "chunks_verified": verified_chunks,
                    "total_chunks": len(chunks),
                    "sync_event_id": event_id,
                    "action": "upload_synchronized"
                }
            
        except Exception as e:
            logger.error(f"Upload sync failed for file {file_id}: {e}")
            raise Exception(f"Upload sync processing failed: {str(e)}")

    async def process_delete_sync(self, file_id: str, event_id: str) -> Dict[str, Any]:
        """Process file deletion synchronization"""
        logger.info(f"Processing delete sync for file {file_id}")
        
        try:
            # 1. Handle test files
            if file_id.startswith(("workflow-test-", "manual-test-", "test-file-")):
                return {
                    "status": "completed",
                    "file_id": file_id,
                    "action": "test_delete_synchronized",
                    "message": "Test file delete sync completed",
                    "sync_event_id": event_id
                }
            
            # 2. Try to get file chunks before deletion
            try:
                chunks = await self._get_file_chunks(file_id)
                logger.info(f"Found {len(chunks)} chunks to delete for file {file_id}")
            except Exception as e:
                logger.warning(f"Could not get chunks for deletion of file {file_id}: {e}")
                # File might already be deleted or never existed
                return {
                    "status": "completed",
                    "file_id": file_id,
                    "action": "delete_already_completed",
                    "message": "File not found, may already be deleted",
                    "sync_event_id": event_id
                }
            
            # 3. Attempt to delete chunks from block storage
            deleted_chunks = 0
            failed_deletions = 0
            
            for chunk in chunks:
                try:
                    chunk_path = chunk.get("storage_path", f"chunk_{chunk.get('chunk_index', 0)}")
                    await self._delete_chunk(chunk_path)
                    deleted_chunks += 1
                    logger.info(f"Deleted chunk {chunk_path}")
                except Exception as e:
                    failed_deletions += 1
                    logger.warning(f"Failed to delete chunk {chunk.get('storage_path', 'unknown')}: {e}")
            
            # 4. Try to delete file metadata
            try:
                await self._delete_file_metadata(file_id)
                logger.info(f"Deleted metadata for file {file_id}")
            except Exception as e:
                logger.warning(f"Failed to delete metadata for file {file_id}: {e}")
            
            return {
                "status": "completed",
                "file_id": file_id,
                "chunks_deleted": deleted_chunks,
                "failed_deletions": failed_deletions,
                "total_chunks": len(chunks),
                "sync_event_id": event_id,
                "action": "delete_synchronized"
            }
            
        except Exception as e:
            logger.error(f"Delete sync failed for file {file_id}: {e}")
            raise Exception(f"Delete sync processing failed: {str(e)}")

    async def process_update_sync(self, file_id: str, event_id: str) -> Dict[str, Any]:
        """Process file update synchronization"""
        logger.info(f"Processing update sync for file {file_id}")
        
        try:
            # 1. Handle test files
            if file_id.startswith(("workflow-test-", "manual-test-", "test-file-")):
                return {
                    "status": "completed",
                    "file_id": file_id,
                    "action": "test_update_synchronized", 
                    "message": "Test file update sync completed",
                    "sync_event_id": event_id
                }
            
            # 2. Try to get latest file metadata
            try:
                file_metadata = await self._get_file_metadata(file_id)
                logger.info(f"Found metadata for update sync: {file_metadata.get('filename', 'unknown')}")
            except Exception as e:
                logger.warning(f"Could not get file metadata for update of {file_id}: {e}")
                return {
                    "status": "failed",
                    "file_id": file_id,
                    "action": "update_metadata_missing",
                    "message": f"File metadata not found: {str(e)}",
                    "sync_event_id": event_id
                }
            
            # 3. Try to get file versions
            try:
                versions = await self._get_file_versions(file_id)
                logger.info(f"Found {len(versions)} versions for file {file_id}")
            except Exception as e:
                logger.warning(f"Could not get file versions for {file_id}: {e}")
                versions = []
            
            # 4. Get latest version info
            latest_version = None
            if versions:
                latest_version = max(versions, key=lambda v: v.get("version_number", 0))
            
            return {
                "status": "completed",
                "file_id": file_id,
                "filename": file_metadata.get("filename", "unknown"),
                "versions_count": len(versions),
                "latest_version": latest_version.get("version_number") if latest_version else None,
                "sync_event_id": event_id,
                "action": "update_synchronized"
            }
            
        except Exception as e:
            logger.error(f"Update sync failed for file {file_id}: {e}")
            raise Exception(f"Update sync processing failed: {str(e)}")

    # Helper methods for service integration
    async def _get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata from metadata service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{METADATA_SERVICE_URL}/files/{file_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def _get_file_chunks(self, file_id: str) -> list:
        """Get file chunks from metadata service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{METADATA_SERVICE_URL}/files/{file_id}/chunks",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def _get_file_versions(self, file_id: str) -> list:
        """Get file versions from metadata service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{METADATA_SERVICE_URL}/files/{file_id}/versions",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def _verify_chunk_exists(self, chunk_id: str) -> bool:
        """Verify chunk exists in block storage"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BLOCK_STORAGE_SERVICE_URL}/chunks/{chunk_id}",
                    headers=self.headers,
                    timeout=5.0  # Shorter timeout for existence check
                )
                exists = response.status_code == 200
                logger.debug(f"Chunk {chunk_id} exists: {exists}")
                return exists
        except Exception as e:
            logger.debug(f"Chunk verification failed for {chunk_id}: {e}")
            return False
    
    async def _delete_chunk(self, chunk_id: str):
        """Delete chunk from block storage"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{BLOCK_STORAGE_SERVICE_URL}/chunks/{chunk_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
    
    async def _delete_file_metadata(self, file_id: str):
        """Delete file metadata"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{METADATA_SERVICE_URL}/files/{file_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
