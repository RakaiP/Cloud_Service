# Cloud File Service Client SDK

A Python client SDK for the Cloud File Service platform. This SDK handles authentication with Auth0 and provides a simple interface to interact with the backend services.

## Installation

```bash
# Install directly from the directory
pip install -e .
```

## Configuration

Set the following environment variables:

```bash
export AUTH0_DOMAIN=your-tenant.auth0.com
export AUTH0_CLIENT_ID=your-client-id
export API_AUDIENCE=https://cloud-api.rakai/
```

Or provide them when initializing the client:

```python
client = CloudServiceClient(
    auth0_domain="your-tenant.auth0.com",
    auth0_client_id="your-client-id",
    auth0_audience="https://cloud-api.rakai/"
)
```

## Usage Example

```python
from cloudservice import CloudServiceClient

# Initialize the client
client = CloudServiceClient()

# Login (opens browser for Auth0 authentication)
client.login()

# Create a file
file = client.create_file("example.txt")
file_id = file["file_id"]
print(f"Created file: {file}")

# List files
files = client.list_files()
print(f"Files: {files}")

# Get file details
file_details = client.get_file(file_id)
print(f"File details: {file_details}")

# Update file
updated_file = client.update_file(file_id, "renamed.txt")
print(f"Updated file: {updated_file}")

# Create a sync event
sync_event = client.create_sync_event(file_id, "upload")
print(f"Sync event: {sync_event}")

# Delete file
client.delete_file(file_id)

# Logout
client.logout()
```

## Authentication

The SDK handles authentication with Auth0:

1. When you call `login()`, it first checks for a saved token
2. If no valid token exists, it opens a browser for Auth0 login
3. After successful login, the token is saved locally
4. The token is automatically attached to all API requests

## Available Methods

### Authentication

- `login()` - Authenticate with Auth0
- `logout()` - Clear saved token

### File Operations

- `create_file(filename)` - Create a new file
- `get_file(file_id)` - Get file metadata
- `list_files(skip, limit)` - List files with pagination
- `update_file(file_id, filename)` - Update file metadata
- `delete_file(file_id)` - Delete a file

### Sync Operations

- `create_sync_event(file_id, event_type)` - Create a sync event
- `get_sync_events(skip, limit, status)` - List sync events
- `get_sync_event(event_id)` - Get sync event details
