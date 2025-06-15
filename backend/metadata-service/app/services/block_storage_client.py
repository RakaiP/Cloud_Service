import requests
import hashlib
import os
from typing import List, Dict, Any, Optional
from io import BytesIO
import httpx
import logging
import re
import asyncio

logger = logging.getLogger(__name__)

class Auth0UserSearchClient:
    """Client for Auth0 Management API user search operations"""
    
    def __init__(self):
        self.auth0_domain = os.getenv("AUTH0_DOMAIN", "")
        self.management_client_id = os.getenv("AUTH0_MANAGEMENT_CLIENT_ID", "")
        self.management_client_secret = os.getenv("AUTH0_MANAGEMENT_CLIENT_SECRET", "")
        self.management_token = None
        self.token_expires_at = 0
        
    async def get_management_token(self) -> str:
        """Get Auth0 Management API token"""
        try:
            import time
            
            # Check if we have a valid token
            if self.management_token and time.time() < self.token_expires_at:
                return self.management_token
            
            # Get new token
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.auth0_domain}/oauth/token",
                    json={
                        "client_id": self.management_client_id,
                        "client_secret": self.management_client_secret,
                        "audience": f"https://{self.auth0_domain}/api/v2/",
                        "grant_type": "client_credentials"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.management_token = token_data["access_token"]
                    self.token_expires_at = time.time() + token_data.get("expires_in", 3600) - 60
                    return self.management_token
                else:
                    logger.warning(f"Failed to get Auth0 management token: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Error getting Auth0 management token: {e}")
            return None
    
    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for users in Auth0"""
        try:
            token = await self.get_management_token()
            if not token:
                logger.warning("No Auth0 management token available, returning demo users")
                return self._get_demo_users(query, limit)
            
            # Search in Auth0
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.auth0_domain}/api/v2/users",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    params={
                        "q": f'email:*{query}* OR name:*{query}*',
                        "search_engine": "v3",
                        "per_page": limit
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    users = response.json()
                    return [
                        {
                            "user_id": user.get("user_id"),
                            "email": user.get("email"),
                            "name": user.get("name", user.get("email", "Unknown")),
                            "picture": user.get("picture", "https://via.placeholder.com/32"),
                            "verified": user.get("email_verified", False),
                            "source": "auth0"
                        }
                        for user in users
                        if user.get("email")  # Only include users with email
                    ]
                else:
                    logger.warning(f"Auth0 user search failed: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"Error searching Auth0 users: {e}")
        
        # Fallback to demo users
        return self._get_demo_users(query, limit)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a specific user by email from Auth0"""
        try:
            token = await self.get_management_token()
            if not token:
                return None
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.auth0_domain}/api/v2/users",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    params={
                        "q": f'email:"{email}"',
                        "search_engine": "v3"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    users = response.json()
                    if users:
                        user = users[0]
                        return {
                            "user_id": user.get("user_id"),
                            "email": user.get("email"),
                            "name": user.get("name", user.get("email", "Unknown")),
                            "picture": user.get("picture", "https://via.placeholder.com/32"),
                            "verified": user.get("email_verified", False),
                            "source": "auth0"
                        }
                        
        except Exception as e:
            logger.warning(f"Error getting user by email from Auth0: {e}")
        
        return None
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return re.match(email_regex, email) is not None
    
    def _get_demo_users(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get demo users for development/testing"""
        demo_users = [
            {
                "user_id": "demo|john.doe",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "picture": "https://via.placeholder.com/32",
                "verified": False,
                "source": "demo"
            },
            {
                "user_id": "demo|jane.smith", 
                "email": "jane.smith@example.com",
                "name": "Jane Smith",
                "picture": "https://via.placeholder.com/32",
                "verified": False,
                "source": "demo"
            },
            {
                "user_id": "demo|bob.wilson",
                "email": "bob.wilson@company.com", 
                "name": "Bob Wilson",
                "picture": "https://via.placeholder.com/32",
                "verified": False,
                "source": "demo"
            },
            {
                "user_id": "demo|alice.johnson",
                "email": "alice.johnson@university.edu",
                "name": "Alice Johnson", 
                "picture": "https://via.placeholder.com/32",
                "verified": False,
                "source": "demo"
            }
        ]
        
        # Filter by query
        if query:
            query_lower = query.lower()
            filtered_users = [
                user for user in demo_users
                if (query_lower in user["name"].lower() or 
                    query_lower in user["email"].lower())
            ]
            return filtered_users[:limit]
        
        return demo_users[:limit]


class BlockStorageClient:
    """Client for interacting with block storage service"""
    
    def __init__(self, base_url: str = "http://block-storage:8000"):
        self.base_url = base_url
    
    async def upload_chunk(self, chunk_id: str, chunk_data: bytes, auth_token: str = None) -> Dict[str, Any]:
        """Upload a chunk to block storage"""
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            files = {"file": (chunk_id, chunk_data, "application/octet-stream")}
            data = {"chunk_id": chunk_id}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chunks",
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
    
    async def download_chunk(self, chunk_id: str, auth_token: str = None) -> bytes:
        """Download a chunk from block storage"""
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/chunks/{chunk_id}",
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.content
                
        except Exception as e:
            logger.error(f"Error downloading chunk {chunk_id}: {e}")
            raise
    
    async def delete_chunk(self, chunk_id: str, auth_token: str = None) -> bool:
        """Delete a chunk from block storage"""
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/chunks/{chunk_id}",
                    headers=headers,
                    timeout=30.0
                )
                return response.status_code in [200, 204, 404]  # 404 is OK (already deleted)
                
        except Exception as e:
            logger.error(f"Error deleting chunk {chunk_id}: {e}")
            return False
