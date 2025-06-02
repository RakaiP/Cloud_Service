@echo off
echo ===== TESTING BLOCK STORAGE ENDPOINTS =====

echo.
echo 1. Testing Health Check...
curl -X GET http://localhost:8003/health

echo.
echo.
echo 2. Testing Stats...
curl -X GET http://localhost:8003/stats

echo.
echo.
echo 3. Testing List Chunks (should be empty initially)...
curl -X GET http://localhost:8003/chunks

echo.
echo.
echo 4. Creating a test file to upload...
echo "This is a test chunk content for MinIO storage" > test-chunk.txt

echo.
echo 5. Uploading test chunk...
curl -X POST http://localhost:8003/chunks -F "file=@test-chunk.txt" -F "chunk_id=test-chunk-001"

echo.
echo.
echo 6. Testing List Chunks (should show our uploaded chunk)...
curl -X GET http://localhost:8003/chunks

echo.
echo.
echo 7. Downloading the chunk...
curl -X GET http://localhost:8003/chunks/test-chunk-001 -o downloaded-chunk.txt

echo.
echo.
echo 8. Verifying downloaded content...
type downloaded-chunk.txt

echo.
echo.
echo 9. Deleting the chunk...
curl -X DELETE http://localhost:8003/chunks/test-chunk-001

echo.
echo.
echo 10. Verifying deletion (list should be empty again)...
curl -X GET http://localhost:8003/chunks

echo.
echo.
echo Cleaning up test files...
del test-chunk.txt downloaded-chunk.txt 2>nul

echo.
echo ===== TESTING COMPLETE =====
pause
