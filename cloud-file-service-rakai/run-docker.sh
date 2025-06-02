#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Build and start services
docker-compose build
docker-compose up -d

echo "Services started!"
echo "Metadata Service: http://localhost:8000"
echo "Sync Service: http://localhost:8001"
echo "Swagger UI: http://localhost:8000/docs and http://localhost:8001/docs"
