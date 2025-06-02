Write-Host "===== TESTING BLOCK STORAGE ENDPOINTS =====" -ForegroundColor Green

# Test Health Check
Write-Host "`n1. Testing Health Check..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "http://localhost:8003/health" -Method Get
$response | ConvertTo-Json

# Test Stats
Write-Host "`n2. Testing Stats..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "http://localhost:8003/stats" -Method Get
$response | ConvertTo-Json

# Test List Chunks
Write-Host "`n3. Testing List Chunks..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "http://localhost:8003/chunks" -Method Get
$response | ConvertTo-Json

# Create test file and upload
Write-Host "`n4. Creating and uploading test chunk..." -ForegroundColor Yellow
"This is a test chunk for PowerShell testing" | Out-File -FilePath "test-chunk.txt" -Encoding UTF8

$form = @{
    file = Get-Item -Path "test-chunk.txt"
    chunk_id = "powershell-test-chunk"
}

$response = Invoke-RestMethod -Uri "http://localhost:8003/chunks" -Method Post -Form $form
$response | ConvertTo-Json

# Download chunk
Write-Host "`n5. Downloading chunk..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "http://localhost:8003/chunks/powershell-test-chunk" -Method Get -OutFile "downloaded-chunk.txt"
Write-Host "Downloaded content:" -ForegroundColor Cyan
Get-Content "downloaded-chunk.txt"

# Delete chunk
Write-Host "`n6. Deleting chunk..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "http://localhost:8003/chunks/powershell-test-chunk" -Method Delete
$response | ConvertTo-Json

# Cleanup
Remove-Item "test-chunk.txt", "downloaded-chunk.txt" -ErrorAction SilentlyContinue
Write-Host "`n===== TESTING COMPLETE =====" -ForegroundColor Green
