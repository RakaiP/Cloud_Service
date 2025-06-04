@echo off
echo ========================================
echo SYNC SERVICE AUTHENTICATION TEST
echo ========================================

echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found
    pause
    exit /b 1
)

echo ✅ Python found

echo.
echo Installing requests...
pip install requests >nul 2>&1

echo.
echo Testing sync service with authentication...
python test-sync-with-auth.py

echo.
echo ========================================
echo TEST COMPLETE
echo ========================================

pause
