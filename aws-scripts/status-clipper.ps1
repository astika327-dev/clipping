# ================================================
# AI Video Clipper - Check Status Script
# ================================================
# Usage: .\status-clipper.ps1
# ================================================

# ========== CONFIGURATION ==========
$INSTANCE_ID = "i-0059a001ba1457303"
$REGION = "ap-southeast-1"

# ========== SCRIPT ==========
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - Instance Status" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get instance details
$INSTANCE_DATA = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --region $REGION `
    --query "Reservations[0].Instances[0]" `
    --output json 2>$null | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Gagal mengambil info instance. Cek kredensial AWS." -ForegroundColor Red
    exit 1
}

$STATUS = $INSTANCE_DATA.State.Name
$INSTANCE_TYPE = $INSTANCE_DATA.InstanceType
$PUBLIC_IP = $INSTANCE_DATA.PublicIpAddress
$LAUNCH_TIME = $INSTANCE_DATA.LaunchTime

# Display status
Write-Host "[INFO] Instance ID    : $INSTANCE_ID" -ForegroundColor White
Write-Host "[INFO] Instance Type  : $INSTANCE_TYPE" -ForegroundColor White

if ($STATUS -eq "running") {
    Write-Host "[OK] Status         : $STATUS" -ForegroundColor Green
    Write-Host "[IP] Public IP      : $PUBLIC_IP" -ForegroundColor Cyan
    Write-Host "[TIME] Launch Time    : $LAUNCH_TIME" -ForegroundColor White
    Write-Host ""
    Write-Host "URL: http://$PUBLIC_IP" -ForegroundColor Green
    Write-Host ""
    Write-Host "[WARN] Instance is RUNNING - biaya compute aktif!" -ForegroundColor Yellow
} elseif ($STATUS -eq "stopped") {
    Write-Host "[STOP] Status         : $STATUS" -ForegroundColor Red
    Write-Host ""
    Write-Host "[SALDO] Instance STOPPED - tidak ada biaya compute." -ForegroundColor Green
    Write-Host "   Jalankan .\start-clipper.ps1 untuk memulai." -ForegroundColor Cyan
} else {
    Write-Host "[WAIT] Status         : $STATUS" -ForegroundColor Yellow
}

Write-Host ""
