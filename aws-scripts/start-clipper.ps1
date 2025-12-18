# ================================================
# AI Video Clipper - Start Instance Script
# ================================================
# Usage: .\start-clipper.ps1
# ================================================

# ========== CONFIGURATION ==========
# Ganti dengan Instance ID kamu (dari AWS Console)
$INSTANCE_ID = "i-0059a001ba1457303"
$REGION = "ap-southeast-1"

# ========== SCRIPT ==========
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - Starting AWS Instance" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "[FAIL] AWS CLI tidak ditemukan!" -ForegroundColor Red
    exit 1
}

# Get current status
Write-Host "[STATUS] Checking status..." -ForegroundColor Yellow
$STATUS = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --region $REGION `
    --query "Reservations[0].Instances[0].State.Name" `
    --output text 2>$null

if ($STATUS -eq "running") {
    Write-Host "[OK] Instance sudah running!" -ForegroundColor Green
    $PUBLIC_IP = aws ec2 describe-instances `
        --instance-ids $INSTANCE_ID `
        --region $REGION `
        --query "Reservations[0].Instances[0].PublicIpAddress" `
        --output text
    Write-Host "URL: http://$PUBLIC_IP" -ForegroundColor Cyan
    Start-Process "http://$PUBLIC_IP"
    exit 0
}

# Start instance
Write-Host "[START] Starting instance..." -ForegroundColor Cyan
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $Region | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Gagal menjalankan instance!" -ForegroundColor Red
    exit 1
}

# Wait for running
Write-Host "[WAIT] Menunggu instance siap (1-2 menit)..." -ForegroundColor Yellow
$spinner = @('|', '/', '-', '\')
$i = 0

do {
    Start-Sleep -Seconds 5
    $STATUS = aws ec2 describe-instances `
        --instance-ids $INSTANCE_ID `
        --region $REGION `
        --query "Reservations[0].Instances[0].State.Name" `
        --output text
    Write-Host "`r   $($spinner[$i % 4]) Status: $STATUS" -NoNewline -ForegroundColor Yellow
    $i++
} while ($STATUS -ne "running")

Write-Host ""

# Get public IP
$PUBLIC_IP = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --region $REGION `
    --query "Reservations[0].Instances[0].PublicIpAddress" `
    --output text

# Wait for services to start
Write-Host "[WAIT] Inisialisasi layanan (30 detik)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   [OK] AI Video Clipper is READY!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "URL: http://$PUBLIC_IP" -ForegroundColor Cyan
Write-Host ""
Write-Host "[WARN] JANGAN LUPA: Jalankan .\stop-clipper.ps1" -ForegroundColor Yellow
Write-Host "       setelah selesai agar saldo tidak habis!" -ForegroundColor Yellow
Write-Host ""

# Open browser
Start-Process "http://$PUBLIC_IP"
