# 🌩️ Cloud File Service - Scalable Microservices Architecture

A complete cloud file service built with **microservices architecture**, featuring file chunking, authentication, and distributed storage.

## 🏆 Project Status: **FULLY FUNCTIONAL** ✅

Successfully handles file upload → chunking → metadata storage → distributed storage with Auth0 authentication.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Auth0 account (for authentication)

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd cloud-file-service-rakai
```

### 2. Configure Auth0
Create `.env` files in each service directory with your Auth0 credentials:
```bash
# Example .env content
AUTH0_DOMAIN=your-tenant.auth0.com
API_AUDIENCE=https://cloud-api.rakai/
```

### 3. Start All Services
```bash
docker compose up -d
```

### 4. Access the Application
- **Frontend**: http://localhost:80
- **API Documentation**: http://localhost:8000/docs

## 🏗️ Architecture

```
Frontend (Port 80)
    ↓ [Auth0 Token + File]
Chunker Service (Port 8002)
    ↓ [Creates metadata]
Metadata Service (Port 8000) → PostgreSQL
    ↓ [Stores chunks]
Block Storage (Port 8003) → MinIO
```

## 🔧 Services Overview

| Service | Port | Purpose | Technology |
|---------|------|---------|------------|
| **Frontend** | 80 | Web UI | HTML/JS + Nginx |
| **Metadata Service** | 8000 | File metadata | FastAPI + PostgreSQL |
| **Sync Service** | 8001 | Synchronization | FastAPI + PostgreSQL |
| **Chunker Service** | 8002 | File orchestration | FastAPI |
| **Block Storage** | 8003 | Chunk storage | FastAPI + MinIO |

## 🎯 Key Features

- ✅ **File Chunking**: Large files split into manageable pieces
- ✅ **Microservices**: Independent, scalable services
- ✅ **Authentication**: Auth0 JWT-based security
- ✅ **Distributed Storage**: MinIO object storage
- ✅ **Metadata Management**: PostgreSQL for file tracking
- ✅ **Real-time UI**: Progressive upload interface
- ✅ **Health Monitoring**: Service health checks
- ✅ **CORS Support**: Cross-origin requests enabled

## 📚 API Documentation

### Chunker Service
- `POST /upload` - Upload and chunk files
- `GET /health` - Health check

### Metadata Service  
- `POST /files` - Create file metadata
- `GET /files` - List files
- `GET /files/{id}` - Get file details

### Block Storage
- `POST /chunks` - Upload chunks
- `GET /chunks/{id}` - Download chunks
- `DELETE /chunks/{id}` - Delete chunks

## 🔒 Authentication

Uses **Auth0** for secure authentication:

1. Get token via Auth0 API
2. Include in `Authorization: Bearer {token}` header
3. All protected endpoints validate JWT

## 🛠️ Development

### Local Development
```bash
# Start individual services
docker compose up metadata-service
docker compose up block-storage
docker compose up chunker-service

# View logs
docker compose logs -f <service-name>
```

### Testing
```bash
# Run tests
docker compose --profile test up test-runner

# Manual API testing
curl -H "Authorization: Bearer <token>" \
     -X POST http://localhost:8002/upload \
     -F "file=@test.pdf"
```

## 📊 Monitoring

- **Health Checks**: All services expose `/health` endpoints
- **Logs**: Structured logging across services
- **MinIO Console**: http://localhost:9001 (admin/admin123)

## 🚀 Deployment

### Production Considerations
1. **Environment Variables**: Set secure Auth0 credentials
2. **Database**: Use managed PostgreSQL
3. **Storage**: Use production MinIO cluster
4. **Load Balancing**: Add nginx/traefik
5. **Monitoring**: Add Prometheus/Grafana

### Scaling
- Each service can be scaled independently
- Database connection pooling configured
- Stateless service design

## 🔧 Configuration

Key environment variables:
```env
# Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
API_AUDIENCE=https://cloud-api.rakai/

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
```

## 📈 Performance

- **Chunk Size**: 1MB (configurable)
- **Max File Size**: 1GB (configurable)
- **Concurrent Uploads**: Supported
- **Database**: Connection pooling enabled

## 🏆 Technical Achievements

This project demonstrates:
- **Microservices Architecture**: Service separation and communication
- **Authentication & Authorization**: JWT-based security
- **File Processing**: Chunking and reconstruction
- **Data Persistence**: Multiple storage backends
- **API Design**: RESTful services with OpenAPI
- **Containerization**: Docker deployment
- **Service Orchestration**: Docker Compose

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

---

**Built with ❤️ for scalable cloud architecture**
