@echo off
echo ===== STARTING CLOUD FILE SERVICES =====

echo 1. Starting PostgreSQL databases...
docker run -d --name metadata-db -p 5432:5432 -e POSTGRES_USER=metadata_user -e POSTGRES_PASSWORD=metadata_password -e POSTGRES_DB=metadata_db postgres:13 2>nul
docker run -d --name sync-db -p 5433:5432 -e POSTGRES_USER=sync_user -e POSTGRES_PASSWORD=sync_password -e POSTGRES_DB=sync_db postgres:13 2>nul

echo 2. Waiting for databases to initialize...
timeout /t 15 /nobreak

echo 3. Starting Metadata Service...
start "Metadata Service" cmd /k "cd backend\metadata-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo 4. Starting Sync Service...
start "Sync Service" cmd /k "cd backend\sync-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

echo.
echo ===== SERVICES STARTED =====
echo Metadata Service: http://localhost:8000
echo Sync Service: http://localhost:8001
echo Health Check: http://localhost:8000/health
echo API Docs: http://localhost:8000/docs
echo.
pause
