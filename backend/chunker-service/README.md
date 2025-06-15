# Chunker Service

A microservice responsible for splitting large files into smaller chunks for efficient storage and retrieval in a distributed cloud file system.

## 📋 Overview

The Chunker Service is a core component of the cloud file service that handles:
- **File Chunking**: Splits large files into manageable 4MB chunks
- **Concurrent Processing**: Handles file upload/download with optimized concurrency
- **Service Orchestration**: Coordinates with metadata, block storage, and sync services
- **Authentication**: Integrates with Auth0 for secure access control

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  Chunker Service │───▶│ Metadata Service│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Block Storage    │
                       │ Service          │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Sync Service     │
                       └──────────────────┘
```

## 🚀 Features

- **Large File Support**: Handles files up to 1GB with 4MB chunk size
- **Concurrent Downloads**: Optimized concurrent chunk downloading for fast file reconstruction
- **Authentication**: JWT token validation with Auth0
- **Health Monitoring**: Built-in health check endpoints
- **Error Handling**: Comprehensive error handling with retry logic
- **Background Processing**: Asynchronous file processing for better performance

## 🛠️ Tech Stack

- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server for FastAPI
- **HTTPx**: Async HTTP client for service communication
- **Python-JOSE**: JWT token handling
- **Aiofiles**: Async file operations

## ⚙️ Environment Variables

Create a `.env` file with the following variables:

```env
# Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain.auth0.com
API_AUDIENCE=https://cloud-api.rakai/
ALGORITHMS=RS256

# Service URLs
METADATA_SERVICE_URL=http://metadata-service:8000
BLOCK_STORAGE_SERVICE_URL=http://block-storage:8003
INDEXER_SERVICE_URL=http://indexer-service:8004

# Chunking Configuration
DEFAULT_CHUNK_SIZE=4194304
MAX_FILE_SIZE=1073741824
```

## 🐳 Docker Setup

### Build and Run

```bash
# Build the Docker image
docker build -t chunker-service .

# Run the container
docker run -p 8002:8002 --env-file .env chunker-service
```

### Docker Compose

```yaml
version: '3.8'
services:
  chunker-service:
    build: .
    ports:
      - "8002:8002"
    environment:
      - AUTH0_DOMAIN=${AUTH0_DOMAIN}
      - API_AUDIENCE=${API_AUDIENCE}
      - METADATA_SERVICE_URL=http://metadata-service:8000
      - BLOCK_STORAGE_SERVICE_URL=http://block-storage:8003
    depends_on:
      - metadata-service
      - block-storage
```

## 📦 Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AUTH0_DOMAIN=your-domain.auth0.com
export API_AUDIENCE=https://cloud-api.rakai/

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## 🔌 API Endpoints

### Health Check
```http
GET /health
```
Returns service health status.

### File Upload
```http
POST /upload
Authorization: Bearer <jwt-token>
Content-Type: multipart/form-data

file: <binary-file-data>
```

**Response:**
```json
{
  "message": "File upload initiated",
  "file_id": "uuid-string",
  "filename": "example.pdf",
  "status": "processing",
  "owner": "user@example.com"
}
```

### File Download
```http
GET /download/{file_id}
Authorization: Bearer <jwt-token>
```

Returns the reconstructed file as a binary stream.

### File Status
```http
GET /files/{file_id}/status
Authorization: Bearer <jwt-token>
```

**Response:**
```json
{
  "file_id": "uuid-string",
  "status": "completed",
  "message": "File processing completed successfully"
}
```

### Service Statistics
```http
GET /stats
Authorization: Bearer <jwt-token>
```

**Response:**
```json
{
  "service": "chunker-service",
  "chunk_size": 4194304,
  "max_file_size": 1073741824,
  "user": "auth0|user-id"
}
```

## 🔧 Configuration

### Chunk Size
Default chunk size is 4MB (4194304 bytes). Modify `DEFAULT_CHUNK_SIZE` environment variable to change.

### Concurrency Settings
The service automatically adjusts concurrent downloads based on file size:
- Small files (≤3 chunks): Download all chunks simultaneously
- Medium files (4-6 chunks): 3 concurrent downloads
- Large files (>6 chunks): 4 concurrent downloads

### File Size Limits
Maximum file size is 1GB by default. Modify `MAX_FILE_SIZE` to change.

## 🏥 Health Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8002/health
```

### Service Dependencies
The service monitors connections to:
- Metadata Service
- Block Storage Service
- Sync Service (optional)
- Indexer Service (optional)

## 🐛 Troubleshooting

### Common Issues

1. **Service Unavailable Errors**
   - Check if dependent services are running
   - Verify service URLs in environment variables
   - Check network connectivity between services

2. **Authentication Failures**
   - Verify Auth0 domain and audience configuration
   - Check JWT token validity and expiration
   - Ensure proper Authorization header format

3. **File Upload Failures**
   - Check file size limits
   - Verify available storage space
   - Review service logs for specific errors

4. **Download Issues**
   - Verify file exists in metadata service
   - Check chunk availability in block storage
   - Review concurrent download settings

### Logging

The service uses structured logging. Log levels:
- `INFO`: General operation information
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors requiring attention
- `DEBUG`: Detailed debugging information

### Performance Monitoring

Monitor these metrics:
- Upload/download throughput (MB/s)
- Chunk processing time
- Concurrent operation success rate
- Service response times

## 🧪 Testing

### Manual Testing

```bash
# Upload a file
curl -X POST "http://localhost:8002/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test-file.pdf"

# Download a file
curl -X GET "http://localhost:8002/download/file-id" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o downloaded-file.pdf
```

### Load Testing

Use tools like Apache Bench or Artillery for load testing:

```bash
# Test upload endpoint
ab -n 10 -c 2 -H "Authorization: Bearer TOKEN" \
  -p test-file.pdf -T multipart/form-data \
  http://localhost:8002/upload
```

## 🚀 Deployment

### Production Considerations

1. **Scaling**: Run multiple instances behind a load balancer
2. **Resource Limits**: Set appropriate CPU and memory limits
3. **Monitoring**: Implement comprehensive monitoring and alerting
4. **Security**: Use HTTPS and secure JWT token handling
5. **Backup**: Ensure chunk data is properly backed up

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chunker-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chunker-service
  template:
    metadata:
      labels:
        app: chunker-service
    spec:
      containers:
      - name: chunker-service
        image: chunker-service:latest
        ports:
        - containerPort: 8002
        env:
        - name: AUTH0_DOMAIN
          valueFrom:
            configMapKeyRef:
              name: auth-config
              key: domain
```

## 📄 License

This project is part of the cloud file service system developed for educational purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review service logs
- Contact the development team

---

**Service Port**: 8002  
**Health Check**: `GET /health`  
**Version**: 1.0.0
