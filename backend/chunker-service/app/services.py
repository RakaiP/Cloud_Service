import httpx
import logging
import os
import asyncio  # ✅ ADD: Missing import for asyncio
from typing import Dict, Any, List
from io import BytesIO

logger = logging.getLogger(__name__)

# Service URLs
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8000")
BLOCK_STORAGE_SERVICE_URL = os.getenv("BLOCK_STORAGE_SERVICE_URL", "http://block-storage:8000")
SYNC_SERVICE_URL = os.getenv("SYNC_SERVICE_URL", "http://sync-service:8000")
INDEXER_SERVICE_URL = os.getenv("INDEXER_SERVICE_URL", "http://indexer-service:8004")

class ServiceIntegration:
    """Handles integration with other microservices"""
    
    def __init__(self, auth_token: str = None):
        self.auth_token = auth_token
        self.headers = {
            "Content-Type": "application/json"
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    def set_auth_token(self, token: str):
        """Update the auth token for requests"""
        self.auth_token = token
        self.headers["Authorization"] = f"Bearer {token}"
    
    async def test_metadata_service(self) -> bool:
        """Test connection to metadata service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{METADATA_SERVICE_URL}/health", timeout=10.0)
                logger.info(f"Metadata service health check: {response.status_code}")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Metadata service test failed: {e}")
            raise
    
    async def create_file_metadata(self, filename: str, owner_user_id: str, owner_email: str = None) -> Dict[str, Any]:
        """Create file metadata in metadata service with proper user info and retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Creating file metadata for: {filename} (owner: {owner_email}) - Attempt {attempt + 1}")
                logger.info(f"Metadata service URL: {METADATA_SERVICE_URL}/files")
                
                payload = {
                    "filename": filename
                }
                logger.info(f"Request payload: {payload}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{METADATA_SERVICE_URL}/files",
                        json=payload,
                        headers=self.headers,
                        timeout=30.0
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    logger.info(f"File metadata created successfully: {result}")
                    return result
                    
            except httpx.ConnectError as e:
                logger.warning(f"❌ Connection failed to metadata service (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("💥 All connection attempts to metadata service failed!")
                    raise Exception("Metadata service unavailable after all retry attempts")
            except Exception as e:
                logger.error(f"Error creating file metadata (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
    
    async def upload_chunk_with_auth(self, chunk_id: str, chunk_data: bytes, auth_header: str) -> Dict[str, Any]:
        """Upload chunk to block storage with authentication"""
        try:
            files = {
                "file": (chunk_id, BytesIO(chunk_data), "application/octet-stream")
            }
            data = {"chunk_id": chunk_id}
            
            headers = {"Authorization": auth_header}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BLOCK_STORAGE_SERVICE_URL}/chunks",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error uploading chunk {chunk_id}: {e}")
            raise
    
    async def create_chunk_metadata(self, file_id: str, chunk_index: int, storage_path: str) -> Dict[str, Any]:
        """Create chunk metadata in metadata service"""
        try:
            payload = {
                "file_id": file_id,
                "chunk_index": chunk_index,
                "storage_path": storage_path
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{METADATA_SERVICE_URL}/files/{file_id}/chunks",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error creating chunk metadata: {e}")
            raise
    
    async def create_file_version(self, file_id: str, storage_path: str) -> Dict[str, Any]:
        """Create file version in metadata service"""
        try:
            payload = {
                "file_id": file_id,
                "storage_path": storage_path
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{METADATA_SERVICE_URL}/files/{file_id}/versions",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error creating file version: {e}")
            raise
    
    async def get_file_download_info(self, file_id: str) -> Dict[str, Any]:
        """Get file download information from metadata service"""
        try:
            logger.info(f"Getting download info for file {file_id}")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{METADATA_SERVICE_URL}/files/{file_id}/download-info",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Download info retrieved: {result}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting download info: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get file info: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error getting file download info: {e}")
            raise

    async def download_chunks_concurrently(self, chunk_ids: List[str], max_concurrent: int = None) -> List[bytes]:
        """
        🚀 SIMPLIFIED CONCURRENT DOWNLOAD: Back to working basics
        """
        
        # 🎯 CONSERVATIVE CONCURRENCY: Start with what works
        if max_concurrent is None:
            if len(chunk_ids) <= 3:
                max_concurrent = len(chunk_ids)  # Small files: download all at once
            elif len(chunk_ids) <= 6:
                max_concurrent = 3  # Medium files: moderate concurrency
            else:
                max_concurrent = 4  # Large files: conservative concurrency
        
        logger.info(f"🔥 Starting SIMPLIFIED CONCURRENT download of {len(chunk_ids)} chunks (max {max_concurrent} concurrent)")
        
        # Create semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_single_chunk_with_order(chunk_id: str, index: int) -> tuple[int, bytes]:
            """Download a single chunk with basic retry logic"""
            async with semaphore:
                retry_count = 0
                max_retries = 2
                
                while retry_count <= max_retries:
                    try:
                        logger.debug(f"⬇️ Downloading chunk {index+1}/{len(chunk_ids)}: {chunk_id}")
                        
                        async with httpx.AsyncClient() as client:
                            response = await client.get(
                                f"{BLOCK_STORAGE_SERVICE_URL}/chunks/{chunk_id}",
                                timeout=10.0  # Simple timeout
                            )
                            response.raise_for_status()
                            data = response.content
                        
                        logger.debug(f"✅ Downloaded chunk {index+1}/{len(chunk_ids)}: {len(data)} bytes")
                        return (index, data)
                        
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"⚠️ Chunk {index+1} download attempt {retry_count} failed: {e}")
                        
                        if retry_count <= max_retries:
                            wait_time = 0.5 * retry_count
                            logger.debug(f"🔄 Retrying chunk {index+1} in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"❌ Failed to download chunk {index+1}/{len(chunk_ids)} after {max_retries + 1} attempts")
                            raise Exception(f"Chunk {index+1} download failed: {str(e)}")
        
        # Create all download tasks
        tasks = [
            download_single_chunk_with_order(chunk_id, index) 
            for index, chunk_id in enumerate(chunk_ids)
        ]
        
        try:
            # 🚀 Execute downloads concurrently
            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()
            
            download_time = end_time - start_time
            total_bytes = sum(len(data) for _, data in results)
            
            logger.info(f"🎉 SIMPLIFIED CONCURRENT DOWNLOAD COMPLETE!")
            logger.info(f"📊 Downloaded {len(chunk_ids)} chunks ({total_bytes} bytes) in {download_time:.2f}s")
            logger.info(f"🚀 Speed: {total_bytes / (1024*1024) / download_time:.2f} MB/s")
            
            # Sort results by original order and extract just the data
            sorted_results = sorted(results, key=lambda x: x[0])
            return [data for _, data in sorted_results]
            
        except Exception as e:
            logger.error(f"❌ Simplified concurrent download failed: {e}")
            raise

    # Keep the old method as fallback
    async def download_chunk(self, chunk_id: str) -> bytes:
        """Download a single chunk from block storage (legacy method for backward compatibility)"""
        try:
            logger.debug(f"Downloading chunk {chunk_id}")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BLOCK_STORAGE_SERVICE_URL}/chunks/{chunk_id}",
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.content
                logger.debug(f"Chunk {chunk_id} downloaded: {len(data)} bytes")
                return data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading chunk {chunk_id}: {e.response.status_code}")
            raise Exception(f"Failed to download chunk: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading chunk {chunk_id}: {e}")
            raise
    
    async def trigger_sync_event(self, file_id: str, event_type: str) -> Dict[str, Any]:
        """Trigger sync event in sync service"""
        try:
            logger.info(f"Triggering {event_type} sync event for file {file_id}")
            payload = {
                "file_id": file_id,
                "event_type": event_type
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SYNC_SERVICE_URL}/sync-events",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Sync event triggered for file {file_id}: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error triggering sync event: {e}")
            raise
    
    async def trigger_indexing(self, file_id: str) -> Dict[str, Any]:
        """Trigger file indexing"""
        try:
            payload = {"file_id": file_id}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{INDEXER_SERVICE_URL}/index",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.warning(f"Failed to index file {file_id}: {e}")
            # Don't raise - indexing is optional
            return {"status": "failed", "error": str(e)}
    
    async def reconstruct_file_from_chunks(self, chunk_ids: List[str]) -> bytes:
        """Download all chunks and reconstruct the original file"""
        try:
            logger.info(f"Reconstructing file from {len(chunk_ids)} chunks")
            
            file_chunks = []
            for i, chunk_id in enumerate(chunk_ids):
                logger.info(f"Downloading chunk {i+1}/{len(chunk_ids)}: {chunk_id}")
                chunk_data = await self.download_chunk(chunk_id)
                file_chunks.append(chunk_data)
                logger.info(f"Downloaded chunk {i+1}, size: {len(chunk_data)} bytes")
            
            # Combine all chunks into single file
            complete_file = b''.join(file_chunks)
            logger.info(f"File reconstruction complete. Total size: {len(complete_file)} bytes")
            
            return complete_file
            
        except Exception as e:
            logger.error(f"Error reconstructing file from chunks: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reconstructing file from chunks: {e}")
            raise
            logger.warning(f"Failed to index file {file_id}: {e}")
            # Don't raise - indexing is optional
            return {"status": "failed", "error": str(e)}
    
    async def reconstruct_file_from_chunks(self, chunk_ids: List[str]) -> bytes:
        """Download all chunks and reconstruct the original file"""
        try:
            logger.info(f"Reconstructing file from {len(chunk_ids)} chunks")
            
            file_chunks = []
            for i, chunk_id in enumerate(chunk_ids):
                logger.info(f"Downloading chunk {i+1}/{len(chunk_ids)}: {chunk_id}")
                chunk_data = await self.download_chunk(chunk_id)
                file_chunks.append(chunk_data)
                logger.info(f"Downloaded chunk {i+1}, size: {len(chunk_data)} bytes")
            
            # Combine all chunks into single file
            complete_file = b''.join(file_chunks)
            logger.info(f"File reconstruction complete. Total size: {len(complete_file)} bytes")
            
            return complete_file
            
        except Exception as e:
            logger.error(f"Error reconstructing file from chunks: {e}")
            raise
            raise
    async def reconstruct_file_from_chunks(self, chunk_ids: List[str]) -> bytes:
        """Download all chunks and reconstruct the original file"""
        try:
            logger.info(f"Reconstructing file from {len(chunk_ids)} chunks")
            
            file_chunks = []
            for i, chunk_id in enumerate(chunk_ids):
                logger.info(f"Downloading chunk {i+1}/{len(chunk_ids)}: {chunk_id}")
                chunk_data = await self.download_chunk(chunk_id)
                file_chunks.append(chunk_data)
                logger.info(f"Downloaded chunk {i+1}, size: {len(chunk_data)} bytes")
            
            # Combine all chunks into single file
            complete_file = b''.join(file_chunks)
            logger.info(f"File reconstruction complete. Total size: {len(complete_file)} bytes")
            
            return complete_file
            
        except Exception as e:
            logger.error(f"Error reconstructing file from chunks: {e}")
            raise
            raise
    
    async def update_file_size(self, file_id: str, file_size: int):
        """Update file size in metadata service"""
        try:
            logger.info(f"Updating file size for {file_id}: {file_size} bytes")
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{METADATA_SERVICE_URL}/files/{file_id}",
                    headers=self.headers,
                    json={"file_size": file_size},
                    timeout=30.0
                )
                response.raise_for_status()
                
                logger.info(f"Successfully updated file size for {file_id}")
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to update file size for {file_id}: {e}")
            # Don't raise here - file size update is not critical for functionality
            # The file will still work without the size being stored
        except Exception as e:
            logger.error(f"Failed to update file size for {file_id}: {e}")
            # Don't raise here - file size update is not critical for functionality
            # The file will still work without the size being stored
