@echo off
echo ===== CHECKING SERVICE STATUS =====

echo 1. Checking PostgreSQL containers...
docker ps --filter "name=metadata-db" --filter "name=sync-db" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo 2. Testing Metadata Service (port 8000)...
curl -s http://localhost:8000/health || echo ERROR: Metadata service not responding

echo.
echo 3. Testing Sync Service (port 8001)...
curl -s http://localhost:8001/ || echo ERROR: Sync service not responding

echo.
echo 4. Checking running processes...
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE 2>nul | findstr "python.exe" || echo No Python processes found

echo.
echo ===== QUICK ACCESS LINKS =====
echo Metadata API: http://localhost:8000/docs
echo Sync API: http://localhost:8001/docs
echo Health Check: http://localhost:8000/health
pause
