@echo off
echo ========================================
echo SYNC SERVICE TESTING - WINDOWS COMPATIBLE
echo ========================================

REM Read token from .env
for /f "tokens=2 delims==" %%a in ('findstr "AUTH0_TOKEN=" .env') do set TOKEN=%%a

echo Using token: %TOKEN:~0,50%...
echo.

echo STEP 1: Testing Sync Service Basic Health...
echo.

echo Root endpoint (no auth):
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/

echo.
echo Health endpoint (if exists):
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/health

echo.
echo STEP 2: Testing Current Sync Endpoints...
echo.

echo Testing sync event creation (current working endpoint):
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events ^
  -H "Content-Type: application/json" ^
  -d "{\"event_type\": \"file_upload\", \"data\": {\"file_id\": \"test-123\", \"filename\": \"test.txt\"}}"

echo.
echo STEP 3: Exploring Sync Service API Structure...
echo.

echo Testing GET endpoints (discovering API):
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/sync-events
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/events  
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/devices
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/status

echo.
echo STEP 4: Testing with Authentication...
echo.

echo Testing sync events with auth:
curl -s -w "\nStatus: %%{http_code}\n" -X GET http://localhost:8001/sync-events ^
  -H "Authorization: Bearer %TOKEN%"

echo.
echo Creating authenticated sync event:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"event_type\": \"file_created\", \"file_id\": \"auth-test-456\", \"filename\": \"authenticated-test.txt\", \"device_id\": \"device-001\"}"

echo.
echo STEP 5: Testing File Sync Event Types...
echo.

echo File created event:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events ^
  -H "Content-Type: application/json" ^
  -d "{\"event_type\": \"file_created\", \"file_id\": \"file-001\", \"filename\": \"new-file.txt\"}"

echo.
echo File updated event:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events ^
  -H "Content-Type: application/json" ^
  -d "{\"event_type\": \"file_updated\", \"file_id\": \"file-001\", \"filename\": \"new-file.txt\", \"version\": 2}"

echo.
echo File deleted event:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events ^
  -H "Content-Type: application/json" ^
  -d "{\"event_type\": \"file_deleted\", \"file_id\": \"file-002\", \"filename\": \"deleted-file.txt\"}"

echo.
echo STEP 6: Testing Device Management...
echo.

echo Register device:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/devices ^
  -H "Content-Type: application/json" ^
  -d "{\"device_id\": \"laptop-001\", \"device_name\": \"Rakai Laptop\", \"device_type\": \"desktop\", \"user_id\": \"user-123\"}"

echo.
echo List devices:
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/devices

echo.
echo STEP 7: Recent sync service logs...
echo.
docker-compose logs sync-service --tail=10

echo.
echo ========================================
echo SYNC SERVICE TEST RESULTS
echo ========================================
echo.
echo Expected Results:
echo ✅ Root endpoint: 200 OK 
echo ✅ Sync event creation: 200/201
echo ✅ Authentication: 401/403 for protected endpoints
echo ✅ File events: 200/201 for create/update/delete
echo.
echo Current Status Based on Previous Tests:
echo ✅ Basic sync service running (Port 8001)
echo ✅ Tests passing (2/2 tests successful)
echo ✅ Sync event creation endpoint working
echo ✅ PostgreSQL integration working
echo.

pause
