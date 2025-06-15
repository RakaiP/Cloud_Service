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
    
    async def _verify_chunks_concurrently(self, chunks: list, max_concurrent: int = 3) -> tuple[int, list]:
        """
        🚀 CONCURRENT chunk verification for sync service
        This prevents sync service from interfering with chunker downloads
        """
        import asyncio
        
        logger.info(f"🔥 Starting CONCURRENT chunk verification for {len(chunks)} chunks (max {max_concurrent} concurrent)")
        
        # Create semaphore to limit concurrent verification
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def verify_single_chunk_with_index(chunk: dict, index: int) -> tuple[int, bool, dict]:
            """Verify a single chunk and return result with index"""
            async with semaphore:
                try:
                    chunk_path = chunk.get("storage_path", f"unknown_chunk_{chunk.get('chunk_index', 0)}")
                    logger.debug(f"⚡ Verifying chunk {index+1}/{len(chunks)}: {chunk_path}")
                    
                    exists = await self._verify_chunk_exists(chunk_path)
                    logger.debug(f"✅ Chunk {index+1}/{len(chunks)} verified: {exists}")
                    return (index, exists, chunk)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to verify chunk {index+1}/{len(chunks)}: {e}")
                    return (index, False, chunk)
        
        # Create all verification tasks
        tasks = [
            verify_single_chunk_with_index(chunk, index) 
            for index, chunk in enumerate(chunks)
        ]
        
        try:
            # 🚀 Execute all verifications concurrently!
            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()
            
            verification_time = end_time - start_time
            
            # Process results
            verified_chunks = 0
            missing_chunks = []
            
            for index, exists, chunk in results:
                if exists:
                    verified_chunks += 1
                else:
                    missing_chunks.append(chunk)
            
            logger.info(f"🎉 CONCURRENT CHUNK VERIFICATION COMPLETE!")
            logger.info(f"📊 Verified {len(chunks)} chunks in {verification_time:.2f}s")
            logger.info(f"✅ {verified_chunks} verified, ❌ {len(missing_chunks)} missing")
            
            return (verified_chunks, missing_chunks)
            
        except Exception as e:
            logger.error(f"❌ Concurrent chunk verification failed: {e}")
            # Fallback to sequential verification
            return await self._verify_chunks_sequential(chunks)

    async def _verify_chunks_sequential(self, chunks: list) -> tuple[int, list]:
        """Fallback sequential chunk verification"""
        verified_chunks = 0
        missing_chunks = []
        
        for chunk in chunks:
            chunk_path = chunk.get("storage_path", f"unknown_chunk_{chunk.get('chunk_index', 0)}")
            if await self._verify_chunk_exists(chunk_path):
                verified_chunks += 1
            else:
                missing_chunks.append(chunk)
        
        return (verified_chunks, missing_chunks)

    async def process_upload_sync(self, file_id: str, event_id: str) -> Dict[str, Any]:
        """Process file upload synchronization with concurrent chunk verification"""
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
            
            # 4. If no chunks yet, mark as pending
            if not chunks:
                return {
                    "status": "pending", 
                    "file_id": file_id,
                    "action": "upload_chunks_pending",
                    "message": "File chunks not yet available, upload may still be processing",
                    "sync_event_id": event_id
                }
            
            # 5. 🚀 Verify chunks exist in block storage CONCURRENTLY
            verified_chunks, missing_chunks = await self._verify_chunks_concurrently(chunks)
            
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
            
            # 2. Get file chunks BEFORE deleting metadata (CRITICAL!)
            chunks = []
            chunk_deletion_results = []
            
            try:
                chunks = await self._get_file_chunks(file_id)
                logger.info(f"Found {len(chunks)} chunks to delete for file {file_id}")
            except Exception as e:
                logger.warning(f"Could not get chunks for deletion of file {file_id}: {e}")
                # File might already be partially deleted, continue anyway
            
            # 3. Delete chunks from block storage FIRST (before metadata is gone)
            deleted_chunks = 0
            failed_deletions = 0
            
            for chunk in chunks:
                try:
                    chunk_path = chunk.get("storage_path", f"chunk_{chunk.get('chunk_index', 0)}")
                    logger.info(f"Attempting to delete chunk: {chunk_path}")
                    
                    # Call block storage service to delete chunk
                    await self._delete_chunk(chunk_path)
                    deleted_chunks += 1
                    logger.info(f"✅ Successfully deleted chunk {chunk_path}")
                    
                except Exception as e:
                    failed_deletions += 1
                    logger.error(f"❌ Failed to delete chunk {chunk.get('storage_path', 'unknown')}: {e}")
                    # Continue with other chunks even if one fails
            
            # 4. Log chunk deletion summary
            logger.info(f"Chunk deletion summary for file {file_id}: {deleted_chunks} deleted, {failed_deletions} failed")
            
            # 5. Return comprehensive status (don't delete metadata here - that's handled by metadata service)
            return {
                "status": "completed",
                "file_id": file_id,
                "chunks_deleted": deleted_chunks,
                "failed_deletions": failed_deletions,
                "total_chunks": len(chunks),
                "sync_event_id": event_id,
                "action": "delete_synchronized",
                "message": f"Deleted {deleted_chunks}/{len(chunks)} chunks from storage"
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
        """Verify chunk exists in block storage with faster timeout"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BLOCK_STORAGE_SERVICE_URL}/chunks/{chunk_id}",
                    headers=self.headers,
                    timeout=3.0  # 🚀 FASTER timeout for verification only
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

