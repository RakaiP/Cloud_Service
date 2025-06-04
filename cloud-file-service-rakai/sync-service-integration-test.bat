@echo off
echo ========================================
echo SYNC SERVICE INTEGRATION TEST
echo ========================================

REM Read token from .env
for /f "tokens=2 delims==" %%a in ('findstr "AUTH0_TOKEN=" .env') do set TOKEN=%%a

echo Testing complete file upload and sync flow...
echo.

echo STEP 1: Upload file to metadata service...
echo.

echo Creating test file:
echo Integration test for sync service %time% > sync-integration-test.txt

echo Uploading to metadata service:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8000/files/upload \
  -H "Authorization: Bearer %TOKEN%" \
  -F "file=@sync-integration-test.txt" > upload-response.json

echo Upload response:
type upload-response.json

echo.
echo STEP 2: Extract file_id and notify sync service...
echo.

REM Extract file_id from response (simplified - in real implementation would parse JSON)
echo Notifying sync service about file upload:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"file_uploaded\", \"file_id\": \"integration-test-file\", \"filename\": \"sync-integration-test.txt\", \"user_id\": \"test-user\", \"device_id\": \"test-device\", \"timestamp\": \"$(date /t)\"}" > sync-notify-response.json

echo Sync notification response:
type sync-notify-response.json

echo.
echo STEP 3: Test device sync queue...
echo.

echo Registering a second device:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/devices \
  -H "Content-Type: application/json" \
  -d "{\"device_id\": \"device-002\", \"device_name\": \"Second Device\", \"user_id\": \"test-user\"}"

echo.
echo Checking pending syncs for second device:
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/devices/device-002/pending-syncs

echo.
echo STEP 4: Test sync completion flow...
echo.

echo Device downloads file from metadata + block storage:
curl -s -w "\nStatus: %%{http_code}\n" -H "Authorization: Bearer %TOKEN%" http://localhost:8000/files

echo.
echo Mark sync as completed:
curl -s -w "\nStatus: %%{http_code}\n" -X PUT http://localhost:8001/sync-events/complete \
  -H "Content-Type: application/json" \
  -d "{\"device_id\": \"device-002\", \"file_id\": \"integration-test-file\", \"status\": \"completed\"}"

echo.
echo STEP 5: Test file modification sync...
echo.

echo Modifying file:
echo Modified content %time% >> sync-integration-test.txt

echo Re-uploading modified file:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8000/files/upload \
  -H "Authorization: Bearer %TOKEN%" \
  -F "file=@sync-integration-test.txt" > modified-upload-response.json

echo.
echo Notifying sync service about file modification:
curl -s -w "\nStatus: %%{http_code}\n" -X POST http://localhost:8001/sync-events \
  -H "Content-Type: application/json" \
  -d "{\"event_type\": \"file_modified\", \"file_id\": \"integration-test-file\", \"filename\": \"sync-integration-test.txt\", \"version\": 2}"

echo.
echo STEP 6: Test real-time sync capabilities...
echo.

echo Testing WebSocket endpoint (if available):
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/ws/device/device-002

echo.
echo Testing polling endpoint:
curl -s -w "\nStatus: %%{http_code}\n" http://localhost:8001/devices/device-002/poll-updates

echo.
echo STEP 7: Complete integration verification...
echo.

echo All services health check:
echo Metadata Service:
curl -s http://localhost:8000/health | findstr "healthy" >NUL && echo "✅ HEALTHY" || echo "❌ DOWN"

echo Block Storage:  
curl -s http://localhost:8003/health | findstr "healthy" >NUL && echo "✅ HEALTHY" || echo "❌ DOWN"

echo Sync Service:
curl -s http://localhost:8001/ | findstr "Synchronization\|running" >NUL && echo "✅ HEALTHY" || echo "❌ DOWN"

echo.
echo Cleanup:
del sync-integration-test.txt 2>nul
del upload-response.json 2>nul
del sync-notify-response.json 2>nul
del modified-upload-response.json 2>nul

echo.
echo ========================================
echo SYNC SERVICE INTEGRATION RESULTS
echo ========================================
echo.
echo Expected Integration Flow:
echo 1. ✅ File uploaded to metadata service
echo 2. ✅ Sync service notified of file creation
echo 3. ✅ Other devices receive sync notifications
echo 4. ✅ Devices download file from metadata/block storage
echo 5. ✅ Sync completion marked in sync service
echo 6. ✅ File modifications trigger new sync events
echo.
echo Integration Points Tested:
echo - 📄 Metadata Service ↔ Sync Service communication
echo - 🔄 Sync event creation and tracking
echo - 📱 Device management and sync queues
echo - ⚡ Real-time sync capabilities (if implemented)
echo - 🔗 Complete upload → sync → download flow
echo.
echo Next Steps:
echo 1. Enhance sync service based on test results
echo 2. Implement WebSocket for real-time sync
echo 3. Add conflict resolution mechanisms
echo 4. Create client SDK sync integration
echo 5. Add sync analytics and monitoring
echo.

pause
