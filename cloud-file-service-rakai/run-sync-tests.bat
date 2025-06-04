@echo off
echo ========================================
echo RUNNING SYNC SERVICE TESTS
echo ========================================

echo Checking if Python is available...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python.
    pause
    exit /b 1
)

echo ✅ Python found

echo.
echo Installing required packages...
pip install requests >nul 2>&1

echo.
echo Running sync service tests...
python sync-service-python-test.py

echo.
echo ========================================
echo Testing completed!
echo ========================================

pause
