@echo off
echo Starting Cloud File Services on localhost...

echo Starting Metadata Service on port 8000...
start cmd /k "cd backend\metadata-service && venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting 3 seconds...
timeout /t 3 /nobreak

echo Starting Sync Service on port 8001...
start cmd /k "cd backend\sync-service && venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

echo Services started!
echo Metadata Service: http://localhost:8000
echo Sync Service: http://localhost:8001
echo Swagger UI: http://localhost:8000/docs and http://localhost:8001/docs
pause
