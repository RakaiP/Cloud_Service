# Sync Service

A microservice responsible for managing synchronization events and coordinating data consistency across the distributed cloud file system.

## 📋 Overview

The Sync Service is a critical component that handles:
- **Event Management**: Records and processes file synchronization events
- **Data Consistency**: Ensures data integrity across distributed components
- **Event Tracking**: Maintains audit trail of all file operations
- **Background Processing**: Handles asynchronous sync operations
- **Authentication**: Integrates with Auth0 for secure access control

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chunker       │───▶│   Sync Service   │───▶│   Database      │
│   Service       │    │                  │    │   (SQLite/      │
└─────────────────┘    └──────────────────┘    │   PostgreSQL)   │
                                │               └─────────────────┘
                                ▼
                       ┌──────────────────┐
                       │ Other Services   │
                       │ (Metadata, etc.) │
                       └──────────────────┘
```

## 🚀 Features

- **Event Processing**: Handles upload, delete, and update events
- **Database Integration**: Supports both SQLite and PostgreSQL
- **RESTful API**: Clean HTTP API for event management
- **Background Tasks**: Asynchronous event processing
- **Health Monitoring**: Built-in health check endpoints
- **Authentication**: JWT token validation with Auth0
- **Testing Suite**: Comprehensive test coverage
- **Docker Support**: Containerized deployment

## 🛠️ Tech Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL/SQLite**: Database backends
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization
- **Python-JOSE**: JWT token handling
- **Pytest**: Testing framework

## ⚙️ Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=sqlite:///./sync.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost/sync_db

# API Configuration
API_TITLE=Synchronization Service API
API_VERSION=1.0.0
API_DESCRIPTION=Service for handling synchronization events

# Security Settings
SECRET_KEY=your_secure_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain.auth0.com
API_AUDIENCE=https://cloud-api.rakai/
ALGORITHMS=RS256

# Service Settings
SYNC_EVENT_PROCESS_INTERVAL=5
```

## 🐳 Docker Setup

### Build and Run

```bash
# Build the Docker image
docker build -t sync-service .

# Run the container
docker run -p 8000:8000 --env-file .env sync-service
```

### Docker Compose

```yaml
version: '3.8'
services:
  sync-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/sync_db
      - AUTH0_DOMAIN=${AUTH0_DOMAIN}
      - API_AUDIENCE=${API_AUDIENCE}
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=sync_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 📦 Local Development

### Prerequisites

- Python 3.11+
- pip
- PostgreSQL (optional, SQLite used by default)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations (if using PostgreSQL)
alembic upgrade head

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Database Setup

#### SQLite (Default)
```bash
# SQLite database is created automatically
# No additional setup required
```

#### PostgreSQL
```bash
# Create database
createdb sync_db

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://username:password@localhost/sync_db

# Run migrations
alembic upgrade head
```

## 🔌 API Endpoints

### Root Endpoint
```http
GET /
```
Returns API information and service status.

**Response:**
```json
{
  "title": "Synchronization Service API",
  "version": "1.0.0",
  "description": "Service for handling synchronization events"
}
```

### Create Sync Event
```http
POST /sync-events
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "file_id": "uuid-string",
  "event_type": "upload"
}
```

**Response:**
```json
{
  "message": "Sync event created successfully",
  "event_id": "event-uuid-string"
}
```

**Event Types:**
- `upload`: File upload completed
- `delete`: File deletion requested
- `update`: File update/modification

### Get Sync Event
```http
GET /sync-events/{event_id}
Authorization: Bearer <jwt-token>
```

**Response:**
```json
{
  "event_id": "event-uuid-string",
  "file_id": "file-uuid-string",
  "event_type": "upload",
  "created_at": "2024-01-15T10:30:00Z",
  "processed": false,
  "processed_at": null
}
```

### List Sync Events
```http
GET /sync-events?limit=10&offset=0
Authorization: Bearer <jwt-token>
```

**Query Parameters:**
- `limit`: Number of events to return (default: 10)
- `offset`: Number of events to skip (default: 0)
- `event_type`: Filter by event type
- `processed`: Filter by processing status

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "sync-service",
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📊 Database Schema

### Sync Events Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| file_id | UUID | File identifier |
| event_type | String | Type of sync event |
| created_at | DateTime | Event creation timestamp |
| processed | Boolean | Processing status |
| processed_at | DateTime | Processing completion timestamp |
| metadata | JSON | Additional event metadata |

## 🔧 Configuration

### Database Configuration

#### SQLite (Development)
```env
DATABASE_URL=sqlite:///./sync.db
```

#### PostgreSQL (Production)
```env
DATABASE_URL=postgresql://user:password@host:port/database
```

### Event Processing
- **SYNC_EVENT_PROCESS_INTERVAL**: How often to process pending events (seconds)
- **ACCESS_TOKEN_EXPIRE_MINUTES**: JWT token expiration time

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app
```

### Docker Testing

```bash
# Build test image
docker build -f Dockerfile.test -t sync-service-test .

# Run tests in container
docker run --rm sync-service-test
```

### Test Coverage

The test suite covers:
- API endpoint functionality
- Database operations
- Event creation and retrieval
- Authentication flows
- Error handling

## 🏥 Health Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

### Monitoring Metrics
- Database connection status
- Event processing queue length
- API response times
- Error rates

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   curl http://localhost:8000/health
   
   # Verify DATABASE_URL format
   echo $DATABASE_URL
   ```

2. **SQLAlchemy Version Issues**
   ```bash
   # Fix SQLAlchemy compatibility
   python fix_sqlalchemy.py
   ```

3. **Authentication Failures**
   - Verify Auth0 domain and audience configuration
   - Check JWT token validity
   - Ensure proper Authorization header format

4. **Migration Issues**
   ```bash
   # Reset database (development only)
   alembic downgrade base
   alembic upgrade head
   ```

### Logging

The service uses structured logging with levels:
- `INFO`: General operations
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors
- `DEBUG`: Detailed debugging

### Performance Optimization

1. **Database Indexing**: Ensure proper indexes on frequently queried fields
2. **Connection Pooling**: Configure appropriate connection pool sizes
3. **Batch Processing**: Process events in batches for better performance

## 🚀 Deployment

### Production Considerations

1. **Database**: Use PostgreSQL for production
2. **Security**: Use strong SECRET_KEY and secure JWT handling
3. **Scaling**: Deploy multiple instances behind load balancer
4. **Monitoring**: Implement comprehensive logging and monitoring
5. **Backup**: Regular database backups

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sync-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sync-service
  template:
    metadata:
      labels:
        app: sync-service
    spec:
      containers:
      - name: sync-service
        image: sync-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: sync-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 📈 API Documentation

### OpenAPI Specification

The service provides OpenAPI documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Integration Examples

#### Python Client
```python
import httpx

async def create_sync_event(file_id: str, event_type: str, token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://sync-service:8000/sync-events",
            json={"file_id": file_id, "event_type": event_type},
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```

#### cURL Examples
```bash
# Create sync event
curl -X POST "http://localhost:8000/sync-events" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "uuid-here", "event_type": "upload"}'

# Get event details
curl -X GET "http://localhost:8000/sync-events/event-id" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📄 License

This project is part of the cloud file service system developed for educational purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review service logs
- Run the health check endpoint
- Check database connectivity
- Contact the development team

---

**Service Port**: 8000  
**Health Check**: `GET /health`  
**API Documentation**: `GET /docs`  
**Version**: 1.0.0
