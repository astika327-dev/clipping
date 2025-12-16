# SSH Port Forwarding Script
# Forward Frontend (5173) dan Backend (5000) dari remote server

$RemoteHost = "root@49.83.140.133"
$RemotePort = 22760
$LocalFrontendPort = 5173
$LocalBackendPort = 5000

Write-Host "=== SSH Port Forwarding ===" -ForegroundColor Green
Write-Host "Remote: $RemoteHost (Port $RemotePort)" -ForegroundColor Yellow
Write-Host "Frontend: localhost:$LocalFrontendPort" -ForegroundColor Yellow
Write-Host "Backend: localhost:$LocalBackendPort" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop forwarding" -ForegroundColor Cyan
Write-Host ""

ssh -p $RemotePort $RemoteHost -L ${LocalFrontendPort}:localhost:${LocalFrontendPort} -L ${LocalBackendPort}:localhost:${LocalBackendPort}
