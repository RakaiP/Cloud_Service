import httpx
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Service URLs
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://localhost:8000")
BLOCK_STORAGE_SERVICE_URL = os.getenv("BLOCK_STORAGE_SERVICE_URL", "http://localhost:8003")
INDEXER_SERVICE_URL = os.getenv("INDEXER_SERVICE_URL", "http://localhost:8004")

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
