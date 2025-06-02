"""
Main client for the Cloud File Service SDK.
"""
import os
import requests
from typing import Dict, List, Optional, Any
import logging

from .auth import Auth0Client

logger = logging.getLogger(__name__)

class CloudServiceClient:
    """
    Client for interacting with the Cloud File Service
    """
    
    def __init__(
        self, 
        metadata_url: str = "http://localhost:8000",
        sync_url: str = "http://localhost:8001",
        auth0_domain: Optional[str] = None,
        auth0_client_id: Optional[str] = None,
        auth0_audience: Optional[str] = None
    ):
        """
        Initialize Cloud Service client
        
        Args:
            metadata_url: URL for metadata service
            sync_url: URL for sync service
            auth0_domain: Auth0 domain (default: from environment)
            auth0_client_id: Auth0 client ID (default: from environment)
            auth0_audience: Auth0 audience (default: from environment)
        """
        self.metadata_url = metadata_url
        self.sync_url = sync_url
        
        # Get Auth0 credentials from parameters or environment
        self.auth0_domain = auth0_domain or os.getenv("AUTH0_DOMAIN")
        self.auth0_client_id = auth0_client_id or os.getenv("AUTH0_CLIENT_ID")
        self.auth0_audience = auth0_audience or os.getenv("API_AUDIENCE")
        
        if not all([self.auth0_domain, self.auth0_client_id, self.auth0_audience]):
            raise ValueError(
                "Auth0 credentials required. Provide as parameters or set environment variables."
            )
        
        # Initialize Auth0 client
        self.auth_client = Auth0Client(
            domain=self.auth0_domain,
            client_id=self.auth0_client_id,
            audience=self.auth0_audience
        )
    
    def login(self) -> bool:
        """
        Authenticate with Auth0
        
        Returns:
            bool: True if login was successful
        """
        return self.auth_client.login()
    
    def logout(self) -> None:
        """Log out and clear token"""
        self.auth_client.logout()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with authorization token
        
        Returns:
            dict: Headers dictionary
        """
        token = self.auth_client.get_access_token()
        if not token:
            raise ValueError("Not authenticated. Call login() first.")
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _request(
        self, 
        method: str, 
        url: str, 
        service: str = "metadata", 
        data: Any = None
    ) -> Any:
        """
        Make an authenticated request to a service
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: URL path
            service: Service to call ("metadata" or "sync")
            data: Request data for POST/PUT requests
            
        Returns:
            Response data (JSON parsed)
        """
        base_url = self.metadata_url if service == "metadata" else self.sync_url
        full_url = f"{base_url}{url}"
        
        headers = self._get_headers()
        
        try:
            if method == "GET":
                response = requests.get(full_url, headers=headers)
            elif method == "POST":
                response = requests.post(full_url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(full_url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(full_url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    # File operations (metadata service)
    
    def create_file(self, filename: str) -> Dict:
        """
        Create a new file
        
        Args:
            filename: Name of the file
            
        Returns:
            dict: Created file data
        """
        return self._request("POST", "/files", data={"filename": filename})
    
    def get_file(self, file_id: str) -> Dict:
        """
        Get file metadata
        
        Args:
            file_id: ID of the file
            
        Returns:
            dict: File metadata
        """
        return self._request("GET", f"/files/{file_id}")
    
    def list_files(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        List files
        
        Args:
            skip: Number of files to skip
            limit: Maximum number of files to return
            
        Returns:
            list: List of file metadata
        """
        return self._request("GET", f"/files?skip={skip}&limit={limit}")
    
    def update_file(self, file_id: str, filename: str) -> Dict:
        """
        Update file metadata
        
        Args:
            file_id: ID of the file
            filename: New filename
            
        Returns:
            dict: Updated file metadata
        """
        return self._request("PUT", f"/files/{file_id}", data={"filename": filename})
    
    def delete_file(self, file_id: str) -> None:
        """
        Delete a file
        
        Args:
            file_id: ID of the file
        """
        self._request("DELETE", f"/files/{file_id}")
    
    # Sync operations (sync service)
    
    def create_sync_event(self, file_id: str, event_type: str) -> Dict:
        """
        Create a sync event
        
        Args:
            file_id: ID of the file
            event_type: Type of event (upload, delete, update)
            
        Returns:
            dict: Created sync event
        """
        data = {
            "file_id": file_id,
            "event_type": event_type
        }
        return self._request("POST", "/sync-events", service="sync", data=data)
    
    def get_sync_events(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Dict]:
        """
        List sync events
        
        Args:
            skip: Number of events to skip
            limit: Maximum number of events to return
            status: Filter by status
            
        Returns:
            list: List of sync events
        """
        url = f"/sync-events?skip={skip}&limit={limit}"
        if status:
            url += f"&status={status}"
        return self._request("GET", url, service="sync")
    
    def get_sync_event(self, event_id: str) -> Dict:
        """
        Get sync event details
        
        Args:
            event_id: ID of the sync event
            
        Returns:
            dict: Sync event details
        """
        return self._request("GET", f"/sync-events/{event_id}", service="sync")
