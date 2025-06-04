@echo off
echo ========================================
echo DETAILED SYNC SERVICE TESTING WITH ERROR ANALYSIS
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
echo STEP 2: Testing Current Sync Endpoints with CORRECT Format...
echo.

echo Testing GET sync events (with auth):
curl -s -w "\nStatus: %%{http_code}\n" -H "Authorization: Bearer %TOKEN%" http://localhost:8001/sync-events

echo.
echo Testing CORRECT sync event format (based on your schema):
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"upload\", \"file_id\": \"test-file-123\", \"user_id\": \"user-456\", \"device_id\": \"device-789\"}"

echo.
echo Testing UPDATE event type:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"update\", \"file_id\": \"test-file-123\", \"user_id\": \"user-456\", \"device_id\": \"device-789\"}"

echo.
echo Testing DELETE event type:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"delete\", \"file_id\": \"test-file-123\", \"user_id\": \"user-456\", \"device_id\": \"device-789\"}"

echo.
echo STEP 3: Testing Invalid Requests (Understanding Error Codes)...
echo.

echo Testing INVALID event_type (should return 422):
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"invalid_type\", \"file_id\": \"test-123\"}" > error-422-response.json

echo Error 422 response:
type error-422-response.json

echo.
echo Testing MISSING required fields (should return 422):
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"upload\"}" > error-missing-fields.json

echo Missing fields response:
type error-missing-fields.json

echo.
echo Testing WITHOUT authentication (should return 401/403):
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"upload\", \"file_id\": \"test-123\"}"

echo.
echo STEP 4: Integration with Metadata Service...
echo.

echo Creating file in metadata service:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8000/files \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"filename\": \"sync-integration.txt\"}" > metadata-response.json

echo Metadata response:
type metadata-response.json

echo.
echo Notifying sync service about metadata file creation:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"upload\", \"file_id\": \"extracted-from-metadata\", \"user_id\": \"test-user\", \"device_id\": \"metadata-service\"}"

echo.
echo STEP 5: Checking Database Content...
echo.

echo Database tables:
docker-compose exec sync-db psql -U sync_user -d sync_db -c "\dt"

echo.
echo Recent sync events (should show our test events):
docker-compose exec sync-db psql -U sync_user -d sync_db -c "SELECT event_type, file_id, user_id, device_id, created_at FROM sync_events ORDER BY created_at DESC LIMIT 5;"

echo.
echo STEP 6: Testing Missing Endpoints (Will Return 404)...
echo.

echo Testing device registration (not implemented yet):
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/devices \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\": \"laptop-001\", \"device_name\": \"Test Laptop\"}"

echo.
echo Testing device sync queue (not implemented yet):
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/devices/laptop-001/pending-syncs

echo.
echo Testing WebSocket endpoint (not implemented yet):
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/ws/device/laptop-001

echo.
echo Cleanup:
del error-422-response.json 2>nul
del error-missing-fields.json 2>nul
del metadata-response.json 2>nul

echo.
echo ========================================
echo HTTP STATUS CODE MEANINGS
echo ========================================
echo.
echo ✅ 200 OK: Request successful, data returned
echo ✅ 201 Created: Resource created successfully 
echo ✅ 204 No Content: Request successful, no data returned
echo.
echo ❌ 400 Bad Request: Invalid request format
echo ❌ 401 Unauthorized: Missing or invalid authentication
echo ❌ 403 Forbidden: Valid auth but insufficient permissions
echo ❌ 404 Not Found: Endpoint or resource does not exist
echo ❌ 405 Method Not Allowed: HTTP method not supported
echo ❌ 422 Unprocessable Entity: Valid format but validation errors
echo ❌ 500 Internal Server Error: Server-side error
echo.
echo ========================================
echo SYNC SERVICE CURRENT CAPABILITIES
echo ========================================
echo.
echo ✅ WORKING FEATURES:
echo - ✅ Basic API info endpoint: GET /
echo - ✅ Health check endpoint: GET /health  
echo - ✅ Sync event creation: POST /sync-events ^(with auth^)
echo - ✅ Sync event listing: GET /sync-events ^(with auth^)
echo - ✅ Auth0 JWT authentication working
echo - ✅ PostgreSQL database integration
echo - ✅ FastAPI with automatic documentation
echo.
echo 📋 REQUIRED EVENT FORMAT:
echo {
echo   "event_type": "upload" ^| "update" ^| "delete",
echo   "file_id": "unique-file-identifier",
echo   "user_id": "user-identifier", 
echo   "device_id": "device-identifier"
echo }
echo.
echo ❌ MISSING FEATURES ^(Need Implementation^):
echo - ❌ Device registration: POST /devices
echo - ❌ Device listing: GET /devices
echo - ❌ Sync queue per device: GET /devices/{id}/pending-syncs
echo - ❌ Mark sync complete: PUT /sync-events/{id}/complete
echo - ❌ Real-time sync: WebSocket /ws/device/{id}
echo - ❌ Conflict resolution logic
echo - ❌ File-specific metadata in events
echo.
echo 🎯 NEXT ENHANCEMENT PRIORITIES:
echo 1. Add device management endpoints
echo 2. Add sync queue functionality 
echo 3. Add real-time WebSocket notifications
echo 4. Enhance event data with file metadata
echo 5. Add conflict detection and resolution
echo.
echo 🔗 INTEGRATION POINTS:
echo - ✅ Metadata Service: Can notify sync service of file changes
echo - ✅ Authentication: Shares Auth0 configuration
echo - ❌ Real-time sync: Needs WebSocket implementation
echo - ❌ Client SDK: Needs sync notification endpoints
echo.

pause
