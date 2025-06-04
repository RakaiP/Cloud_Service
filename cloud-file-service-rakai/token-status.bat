@echo off
echo ========================================
echo CHECKING AUTH0 TOKEN STATUS
echo ========================================

SET TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkxkZ0lUSm1wOGNzSnFlelNHTVZMaiJ9.eyJpc3MiOiJodHRwczovL2Rldi1tYzcyMWJ3M3o3MnQzeGV4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJMYnpzdXNWclQ3SHFGRldmM2hrbXJSTUtLZFJxRW9qY0BjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly9jbG91ZC1hcGkucmFrYWkvIiwiaWF0IjoxNzQ5MDExMTcxLCJleHAiOjE3NDkwOTc1NzEsImd0eSI6ImNsaWVudC1jcmVkZW50aWFscyIsImF6cCI6IkxienN1c1ZyVDdIcUZGV2YzaGttclJNS0tkUnFFb2pjIn0.dWIwq7gnwVDt5A9fUZ98Ycj6XqMWtbZjnBKmTN8hXMQ7-oisY490qG7w1DKJI1w_OB__VaFVjrQis8y7SuVyZiCs21LZV84xslFtFiXPYkSRSVEfo5x3vBX4Q8EessZn3NccHsn2NPi3EQgn-8K-Aa5FRdd-DBuurxeDL39koshbzr0Z6LjjR7RNioGoW7ZasjxKH4liTbHHTN-V77_gKUz0y-dJo5L4LsV6Q3l4lSiDy1CfRMbNHZUrIxtZRlAG82v8tuaI6jYcOlUtf90lF6Ww25qWvwpPHG0wwN0HARJAaZTk-zY2fjvk5GnfqTL6i9UEvNJB-wVP9D9elC4tvQ

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
