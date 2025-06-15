# Block Storage Service

FastAPI service for storing file chunks locally on disk as part of the cloud file sharing system.

## Purpose
- Stores actual chunk data (file contents)
- Provides REST endpoints for chunk upload/download/delete
- Works with metadata-service and sync-service for complete file management

## Local Storage Structure
```
storage/
├── {file_id}_{chunk_index}_{uuid}.chunk
├── {file_id}_{chunk_index}_{uuid}.chunk
└── ...
```

## Running the Service
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m src.main
```

Service runs on http://localhost:8003

## API Endpoints
- POST /chunks - Upload a file chunk
- GET /chunks/{chunk_id} - Download a chunk by ID  
- DELETE /chunks/{chunk_id} - Delete a chunk by ID

## Integration
- Metadata service stores chunk_id and storage_path references
- Client SDK uploads chunks here after creating file metadata
- Sync service coordinates file changes across devices
