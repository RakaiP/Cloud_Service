import httpx
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Service URLs
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://localhost:8000")
BLOCK_STORAGE_SERVICE_URL = os.getenv("BLOCK_STORAGE_SERVICE_URL", "http://localhost:8003")
INDEXER_SERVICE_URL = os.getenv("INDEXER_SERVICE_URL", "http://localhost:8004")
SYNC_SERVICE_URL = os.getenv("SYNC_SERVICE_URL", "http://sync-service:8000")

class ServiceIntegration:
    """Handles integration with other microservices"""
    
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    async def test_metadata_service(self) -> bool:
        """Test if metadata service is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{METADATA_SERVICE_URL}/health",
                    timeout=10.0
                )
                logger.info(f"Metadata service health check: {response.status_code}")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Metadata service health check failed: {e}")
            return False
    
    async def create_file_metadata(self, filename: str) -> Dict[str, Any]:
        """Create file metadata in metadata service"""
        try:
            logger.info(f"Creating file metadata for: {filename}")
            
            # First test if the service is accessible
            if not await self.test_metadata_service():
                raise Exception("Metadata service is not accessible")
            
            # Log the request details
            logger.info(f"Metadata service URL: {METADATA_SERVICE_URL}/files")
            logger.info(f"Request headers: {self.headers}")
            logger.info(f"Request payload: {{'filename': '{filename}'}}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{METADATA_SERVICE_URL}/files",
                    json={"filename": filename},
                    headers=self.headers,
                    timeout=30.0
                )
                
                logger.info(f"Metadata service response: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                # Log response content for debugging
                response_text = response.text
                logger.info(f"Response content: {response_text}")
                
                if response.status_code == 401:
                    logger.error("Authentication failed with metadata service")
                    logger.error(f"Request headers: {self.headers}")
                    raise httpx.HTTPStatusError(
                        "Authentication failed with metadata service",
                        request=response.request,
                        response=response
                    )
                elif response.status_code == 500:
                    logger.error("Metadata service internal error")
                    logger.error(f"Response: {response_text}")
                    raise httpx.HTTPStatusError(
                        f"Metadata service internal error: {response_text}",
                        request=response.request,
                        response=response
                    )
                
                response.raise_for_status()
                result = response.json()
                logger.info(f"File metadata created successfully: {result}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating file metadata: {e}")
            logger.error(f"Response content: {e.response.text if e.response else 'No response'}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout creating file metadata: {e}")
            raise Exception("Metadata service timeout")
        except Exception as e:
            logger.error(f"Unexpected error creating file metadata: {e}")
            raise
    
    async def create_chunk_metadata(self, file_id: str, chunk_index: int, storage_path: str) -> Dict[str, Any]:
        """Create chunk metadata in metadata service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{METADATA_SERVICE_URL}/files/{file_id}/chunks",
                    json={
                        "file_id": file_id,
                        "chunk_index": chunk_index,
                        "storage_path": storage_path
                    },
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating chunk metadata: {e}")
            raise
    
    async def upload_chunk_to_storage(self, chunk_data: bytes, chunk_id: str) -> Dict[str, Any]:
        """Upload chunk to block storage service"""
        try:
            async with httpx.AsyncClient() as client:
                files = {
                    "file": (chunk_id, chunk_data, "application/octet-stream")
                }
                data = {
                    "chunk_id": chunk_id
                }
                
                # Remove content-type from headers for multipart upload
                upload_headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                response = await client.post(
                    f"{BLOCK_STORAGE_SERVICE_URL}/chunks",
                    files=files,
                    data=data,
                    headers=upload_headers,
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error uploading chunk to storage: {e}")
            raise
    
    async def index_file(self, file_id: str, filename: str, content_type: str, size: int, file_hash: str) -> Dict[str, Any]:
        """Index file in indexer service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{INDEXER_SERVICE_URL}/index",
                    json={
                        "file_id": file_id,
                        "filename": filename,
                        "content_type": content_type,
                        "size": size,
                        "file_hash": file_hash
                    },
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to index file {file_id}: {e}")
            # Don't fail the upload if indexing fails
            return {"status": "indexing_failed", "error": str(e)}
    
    async def create_file_version(self, file_id: str, storage_path: str) -> Dict[str, Any]:
        """Create a new version of the file"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{METADATA_SERVICE_URL}/files/{file_id}/versions",
                    json={
                        "file_id": file_id,
                        "storage_path": storage_path
                    },
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating file version: {e}")
            raise
    
    async def trigger_sync_event(self, file_id: str, event_type: str, description: str = None) -> Dict[str, Any]:
        """Trigger a sync event in the sync service"""
        try:
            logger.info(f"Triggering {event_type} sync event for file {file_id}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SYNC_SERVICE_URL}/sync-events",
                    json={
                        "file_id": file_id,
                        "event_type": event_type
                    },
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Sync event triggered for file {file_id}: {result}")
                return result
        except Exception as e:
            logger.warning(f"Failed to trigger sync event for file {file_id}: {e}")
            # Don't fail the main operation if sync fails
            return {"status": "sync_failed", "error": str(e)}
    
    async def get_file_download_info(self, file_id: str) -> Dict[str, Any]:
        """Get file download information from metadata service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{METADATA_SERVICE_URL}/files/{file_id}/download-info",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting file download info: {e}")
            raise

    async def download_chunk_from_storage(self, chunk_id: str) -> bytes:
        """Download a single chunk from block storage"""
        try:
            async with httpx.AsyncClient() as client:
                # Remove content-type for GET request
                download_headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                response = await client.get(
                    f"{BLOCK_STORAGE_SERVICE_URL}/chunks/{chunk_id}",
                    headers=download_headers,
                    timeout=60.0
                )
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading chunk {chunk_id}: {e}")
            raise

    async def reconstruct_file_from_chunks(self, chunk_ids: List[str]) -> bytes:
        """Download all chunks and reconstruct the original file"""
        try:
            logger.info(f"Reconstructing file from {len(chunk_ids)} chunks")
            
            file_chunks = []
            for i, chunk_id in enumerate(chunk_ids):
                logger.info(f"Downloading chunk {i+1}/{len(chunk_ids)}: {chunk_id}")
                chunk_data = await self.download_chunk_from_storage(chunk_id)
                file_chunks.append(chunk_data)
                logger.info(f"Downloaded chunk {i+1}, size: {len(chunk_data)} bytes")
            
            # Combine all chunks into single file
            complete_file = b''.join(file_chunks)
            logger.info(f"File reconstruction complete. Total size: {len(complete_file)} bytes")
            
            return complete_file
            
        except Exception as e:
            logger.error(f"Error reconstructing file from chunks: {e}")
            raise
