"""
Example usage of the Cloud File Service Client SDK
"""
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add the parent directory to the path so we can import the package directly
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cloudservice import CloudServiceClient

def main():
    """Run a demo of the client SDK"""
    # Initialize client (using environment variables for Auth0 credentials)
    client = CloudServiceClient(
        metadata_url="http://localhost:8000",
        sync_url="http://localhost:8001"
    )
    
    print("\n=== Cloud File Service Demo ===\n")
    
    # Login with Auth0
    print("Logging in...")
    if not client.login():
        print("Login failed. Exiting.")
        return
    
    print("Login successful!")
    
    try:
        # Create a file
        print("\nCreating a new file...")
        file = client.create_file("example.txt")
        file_id = file["file_id"]
        print(f"Created file: {file}")
        
        # List files
        print("\nListing all files...")
        files = client.list_files()
        print(f"Files: {files}")
        
        # Get file details
        print(f"\nGetting details for file {file_id}...")
        file_details = client.get_file(file_id)
        print(f"File details: {file_details}")
        
        # Update file
        print(f"\nUpdating file {file_id}...")
        updated_file = client.update_file(file_id, "renamed.txt")
        print(f"Updated file: {updated_file}")
        
        # Create a sync event
        print(f"\nCreating sync event for file {file_id}...")
        sync_event = client.create_sync_event(file_id, "upload")
        event_id = sync_event["event_id"]
        print(f"Created sync event: {sync_event}")
        
        # Get sync event details
        print(f"\nGetting details for sync event {event_id}...")
        event_details = client.get_sync_event(event_id)
        print(f"Sync event details: {event_details}")
        
        # Wait for the sync event to be processed
        print("\nWaiting for the sync event to be processed...")
        time.sleep(2)
        
        # Get updated sync event details
        print(f"\nGetting updated details for sync event {event_id}...")
        updated_event = client.get_sync_event(event_id)
        print(f"Updated sync event details: {updated_event}")
        
        # Delete the file
        print(f"\nDeleting file {file_id}...")
        client.delete_file(file_id)
        print("File deleted successfully")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Logout
    print("\nLogging out...")
    client.logout()
    print("Logged out successfully")
    
    print("\nDemo completed!")

if __name__ == "__main__":
    main()

# This script demonstrates how to use the Cloud File Service Client SDK.
from client_sdk.uploader import upload_file
from client_sdk.downloader import download_file

upload_file("bigfile.zip", "http://server.com/upload", chunk_size=1024*1024)
download_file("http://server.com/download", num_chunks=10, output_path="restored.zip")
# This script uploads a file in chunks and downloads it back, demonstrating the chunking functionality.