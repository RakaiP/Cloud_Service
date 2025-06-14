@echo off
echo ========================================
echo CHECKING AUTH0 TOKEN STATUS
echo ========================================

SET TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkxkZ0lUSm1wOGNzSnFlelNHTVZMaiJ9.eyJpc3MiOiJodHRwczovL2Rldi1tYzcyMWJ3M3o3MnQzeGV4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJMYnpzdXNWclQ3SHFGRldmM2hrbXJSTUtLZFJxRW9qY0BjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly9jbG91ZC1hcGkucmFrYWkvIiwiaWF0IjoxNzQ5ODU4NjE1LCJleHAiOjE3NDk5NDUwMTUsImd0eSI6ImNsaWVudC1jcmVkZW50aWFscyIsImF6cCI6IkxienN1c1ZyVDdIcUZGV2YzaGttclJNS0tkUnFFb2pjIn0.SxY7D4OH3eQHW6xnbVU8WUzjAX0l98t65k4ieyWI7UVAcLVENzq461y8Koo0dGsDhuTIUpcJo1_w2tV5VKM-0Brmf2VPIqN8ZPc8hpkVYVjf69Z2jw1EK13FyUPmTmRXRTRYUUz74CD8XCSr9KBkXqWXAzBIHplT4mEiYZVyf5JZW9tcMI8XCbEjAg6YeBJT3x6Fy9ckqPpiiNZkwFMItzc-abZmfYMY0_7Vc6_sLNyNPxu5wTaU6_v7hsEXQqJBx4nIg2MbrcHjDCep_wieZ-_HKWnDZzTuv3FQUexbcP2Zo_6XM57LVcfvUJy2iybnPpmntL1WIqtjMB559e8hUA

echo.
echo Token Info:
echo Issued: 2024-12-05 (iat: 1749011171)
echo Expires: 2024-12-06 (exp: 1749097571)
echo Subject: Machine-to-Machine Client
echo Audience: https://cloud-api.rakai/
echo.

echo Current time check:
echo %date% %time%

echo.
echo Testing token with different endpoints:
echo.

echo 1. Health (no auth needed):
curl -s -w "Status: %%{http_code}\n" http://localhost:8000/health

echo.
echo 2. Files list (requires auth):
curl -s -w "Status: %%{http_code}\n" -H "Authorization: Bearer %TOKEN%" http://localhost:8000/files

echo.
echo 3. Block storage (no auth):
curl -s -w "Status: %%{http_code}\n" http://localhost:8003/health

echo.
echo ========================================
echo TOKEN STATUS ANALYSIS
echo ========================================
echo.
echo ✅ If files list returns 200 + JSON: Token is valid
echo ✅ If files list returns 401: Token expired - get new one
echo ❌ If files list returns 500: Server error (not token issue)
echo ❌ If files list returns 403: Token valid but permissions issue
echo.
echo To get a new token:
echo 1. Go to: https://manage.auth0.com/dashboard
echo 2. APIs > https://cloud-api.rakai/ > Test tab
echo 3. Copy new access_token
echo.

pause
