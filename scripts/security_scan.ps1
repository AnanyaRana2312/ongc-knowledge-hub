# scripts/security_scan.ps1
$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " ONGC Knowledge Hub - Security Scan (Trivy) " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Write-Host "`n[1/3] Pulling the latest Trivy image..." -ForegroundColor Yellow
docker pull aquasec/trivy:latest

# Note: In Windows, the docker socket is mounted differently sometimes, but Docker Desktop supports this
$ReportFile = "security_report.txt"

Write-Host "`n[2/3] Scanning Backend Container Image..." -ForegroundColor Yellow
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image ongc-knowledge-hub-backend:latest --severity HIGH,CRITICAL --no-progress | Tee-Object -FilePath $ReportFile

Write-Host "`n[3/3] Scanning Frontend Container Image..." -ForegroundColor Yellow
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image ongc-knowledge-hub-frontend:latest --severity HIGH,CRITICAL --no-progress | Tee-Object -FilePath $ReportFile -Append

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host " Scan Complete! Results saved to $ReportFile" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
