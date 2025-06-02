#!/bin/bash

echo "===== DEBUGGING DOCKER CONTAINERS ====="

# Stop any running containers
echo "Stopping any existing containers..."
docker-compose down

# Remove any dangling images
echo "Cleaning up..."
docker system prune -f

# Check if .env file exists and has valid contents
echo "Checking .env file..."
if [ ! -f .env ]; then
  echo "ERROR: .env file missing!"
else
  echo "OK: .env file exists"
fi

# Build with verbose output
echo "Building containers with verbose output..."
docker-compose build --no-cache

# Start with logs
echo "Starting containers and showing logs..."
docker-compose up
