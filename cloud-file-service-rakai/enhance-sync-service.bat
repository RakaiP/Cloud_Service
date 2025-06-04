@echo off
echo ========================================
echo ENHANCING SYNC SERVICE FOR FILE STORAGE
echo ========================================

echo.
echo STEP 1: Analyzing current sync service structure...
echo.

echo Current sync service files:
dir "backend\sync-service" /B 2>nul || echo "Sync service directory not found"

echo.
echo Current sync service endpoints (from logs):
docker-compose logs sync-service --tail=10 | findstr "INFO" | findstr "GET\|POST\|PUT\|DELETE"

echo.
echo STEP 2: Testing current sync service capabilities...
echo.

echo Basic functionality test:
curl -s -w "Status: %%{http_code}\n" http://localhost:8001/

echo.
echo Current sync event creation:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"test_enhancement\", \"data\": {\"test\": \"enhancement_phase\"}}" > sync-response.json

echo Response:
type sync-response.json

echo.
echo STEP 3: Planning sync service enhancements...
echo.

echo Creating enhancement plan file...
echo # SYNC SERVICE ENHANCEMENT PLAN > sync-enhancement-plan.md
echo. >> sync-enhancement-plan.md
echo ## Current Status: >> sync-enhancement-plan.md
echo ✅ Basic FastAPI service running on Port 8001 >> sync-enhancement-plan.md
echo ✅ PostgreSQL database connection working >> sync-enhancement-plan.md
echo ✅ Basic sync event creation endpoint >> sync-enhancement-plan.md
echo ✅ Tests passing (2/2) >> sync-enhancement-plan.md
echo. >> sync-enhancement-plan.md
echo ## Enhancement Phase 1: File Sync Events >> sync-enhancement-plan.md
echo - [ ] File upload/created events >> sync-enhancement-plan.md
echo - [ ] File modified/updated events >> sync-enhancement-plan.md
echo - [ ] File deleted events >> sync-enhancement-plan.md
echo - [ ] File moved/renamed events >> sync-enhancement-plan.md
echo. >> sync-enhancement-plan.md
echo ## Enhancement Phase 2: Device Management >> sync-enhancement-plan.md
echo - [ ] Device registration endpoint >> sync-enhancement-plan.md
echo - [ ] Device status tracking >> sync-enhancement-plan.md
echo - [ ] User-device associations >> sync-enhancement-plan.md
echo. >> sync-enhancement-plan.md
echo ## Enhancement Phase 3: Sync Queue >> sync-enhancement-plan.md
echo - [ ] Per-device sync queues >> sync-enhancement-plan.md
echo - [ ] Pending sync operations >> sync-enhancement-plan.md
echo - [ ] Sync status tracking >> sync-enhancement-plan.md
echo - [ ] Conflict detection >> sync-enhancement-plan.md

echo ✅ Enhancement plan created: sync-enhancement-plan.md

echo.
echo STEP 4: Testing integration with metadata service...
echo.

REM Read token from .env
for /f "tokens=2 delims==" %%a in ('findstr "AUTH0_TOKEN=" .env') do set TOKEN=%%a

echo Creating a file in metadata service:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8000/files \
  -H "Authorization: Bearer %TOKEN%" \
  -H "Content-Type: application/json" \
  -d "{\"filename\": \"sync-integration-test.txt\"}" > metadata-file-response.json

echo Metadata service response:
type metadata-file-response.json

echo.
echo Notifying sync service about the file creation:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"file_created\", \"file_id\": \"extracted_from_metadata\", \"filename\": \"sync-integration-test.txt\", \"source_service\": \"metadata-service\"}"

echo.
echo STEP 5: Testing sync service database structure...
echo.

echo Checking sync database tables:
docker-compose exec sync-db psql -U sync_user -d sync_db -c "\dt" 2>nul || echo "Cannot access database - service might need restart"

echo.
echo STEP 6: Proposing sync service enhancements...
echo.

echo ========================================
echo SYNC SERVICE ENHANCEMENT RECOMMENDATIONS
echo ========================================
echo.
echo 🎯 IMMEDIATE ENHANCEMENTS NEEDED:
echo.
echo 1. FILE-SPECIFIC SYNC EVENTS:
echo    - Add file_id, filename, file_size to sync events
echo    - Support event types: file_created, file_updated, file_deleted
echo    - Include timestamp and user_id for tracking
echo.
echo 2. DEVICE MANAGEMENT:
echo    - POST /devices ^(register device^)
echo    - GET /devices ^(list user devices^)  
echo    - PUT /devices/{device_id}/status ^(update device status^)
echo.
echo 3. SYNC QUEUE PER DEVICE:
echo    - GET /devices/{device_id}/pending-syncs
echo    - POST /devices/{device_id}/sync-complete
echo    - DELETE /devices/{device_id}/clear-queue
echo.
echo 4. INTEGRATION WITH METADATA SERVICE:
echo    - Webhook endpoint for metadata service to notify sync
echo    - Sync service calls metadata service to get file details
echo    - Real-time notifications to other devices
echo.
echo 5. REAL-TIME SYNC FEATURES:
echo    - WebSocket endpoint: /ws/device/{device_id}
echo    - Polling endpoint: /devices/{device_id}/poll-updates
echo    - Push notifications for instant sync
echo.

echo Cleanup:
del sync-response.json 2>nul
del metadata-file-response.json 2>nul

echo.
echo 🚀 READY TO ENHANCE SYNC SERVICE!
echo Run the detailed test first: test-sync-service-detailed.bat
echo Then implement enhancements based on the results.
echo.

pause
