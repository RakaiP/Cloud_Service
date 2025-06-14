# Metadata Service

This service manages file metadata, versioning, and chunking for the cloud file service platform.

## Features

- File metadata storage and retrieval
- File versioning system
- Support for chunked file uploads
- RESTful API following OpenAPI standards

## Running with Docker

### Prerequisites

- Docker and Docker Compose installed on your system

### Starting the service

```bash
# Start both the metadata service and its PostgreSQL database
docker-compose up

# Run in detached mode
docker-compose up -d
```

The API will be available at http://localhost:8000 with interactive documentation at http://localhost:8000/docs.

### Stopping the service

```bash
docker-compose down
```

## Running without Docker

### Prerequisites

- Python 3.8+ installed
- PostgreSQL database (optional, can use SQLite for development)

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the `DATABASE_URL` if needed

4. Run the service:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /files` - Create file metadata
- `GET /files` - List all files
- `GET /files/{file_id}` - Get file metadata
- `PUT /files/{file_id}` - Update file metadata
- `DELETE /files/{file_id}` - Delete file
- `POST /files/{file_id}/versions` - Create file version
- `GET /files/{file_id}/versions` - List file versions
- `POST /files/{file_id}/chunks` - Create file chunk
- `GET /files/{file_id}/chunks` - List file chunks

## Integration with other microservices

This metadata service is part of a larger cloud file service platform, working alongside:

- Block Storage Service - Handles actual file storage
- Sync Service - Manages file synchronization
- User Auth Service - Handles authentication and authorization

<<<<<<< HEAD
The services communicate through RESTful APIs and can be orchestrated together using the root `docker-compose.yml` file.
=======
The services communicate through RESTful APIs and can be orchestrated together using the root `docker-compose.yml` file.
>>>>>>> ba2b2eb56daca6d9c07df4f6c3b896b654bdab6e
