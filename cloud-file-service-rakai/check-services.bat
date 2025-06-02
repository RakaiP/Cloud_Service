@echo off
echo ===== CHECKING SERVICE STATUS =====

echo Checking all services...
docker-compose ps

echo.
echo Testing endpoints...
curl -s http://localhost:8000/health || echo ERROR: Metadata service down
curl -s http://localhost:8001/ || echo ERROR: Sync service down  
curl -s http://localhost:8003/health || echo ERROR: Block storage down
curl -s http://localhost:9000/minio/health/live || echo ERROR: MinIO down

echo.
echo ===== ACCESS LINKS =====
echo Metadata API: http://localhost:8000/docs
echo Sync API: http://localhost:8001/docs
echo Block Storage API: http://localhost:8003/docs
echo MinIO Console: http://localhost:9001
pause
