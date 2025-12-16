# ================================================
# AI Video Clipper - Stop Instance Script
# ================================================
# Usage: .\stop-clipper.ps1
# ================================================

# ========== CONFIGURATION ==========
# Ganti dengan Instance ID kamu (dari AWS Console)
$INSTANCE_ID = "i-XXXXXXXXXXXXX"  # <-- GANTI INI!
$REGION = "ap-southeast-1"        # <-- Sesuaikan region

# ========== SCRIPT ==========
Write-Host ""
Write-Host "================================================" -ForegroundColor Red
Write-Host "   AI Video Clipper - Stopping AWS Instance" -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red
Write-Host ""

# Check if Instance ID is configured
if ($INSTANCE_ID -eq "i-XXXXXXXXXXXXX") {
    Write-Host "❌ ERROR: Instance ID belum dikonfigurasi!" -ForegroundColor Red
    Write-Host "   Edit file ini dan ganti INSTANCE_ID dengan ID instance kamu." -ForegroundColor Yellow
    exit 1
}

# Get current status
Write-Host "📊 Checking current status..." -ForegroundColor Yellow
$STATUS = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --region $REGION `
    --query "Reservations[0].Instances[0].State.Name" `
    --output text 2>$null

if ($STATUS -eq "stopped") {
    Write-Host "✅ Instance sudah stopped. Tidak ada biaya compute." -ForegroundColor Green
    exit 0
}

if ($STATUS -ne "running") {
    Write-Host "⚠️  Instance status: $STATUS" -ForegroundColor Yellow
    Write-Host "   Instance tidak dalam status running." -ForegroundColor Yellow
    exit 0
}

# Confirm stop
Write-Host "🛑 Instance saat ini RUNNING." -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Yakin ingin STOP instance? (y/N)"

if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "❌ Cancelled." -ForegroundColor Yellow
    exit 0
}

# Stop instance
Write-Host ""
Write-Host "🛑 Stopping instance..." -ForegroundColor Cyan
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to stop instance!" -ForegroundColor Red
    exit 1
}

# Wait for stopped
Write-Host "⏳ Waiting for instance to stop..." -ForegroundColor Yellow
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
} while ($STATUS -ne "stopped")

Write-Host ""
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   ✅ Instance STOPPED Successfully!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "💰 Tidak ada biaya compute lagi!" -ForegroundColor Cyan
Write-Host "   Storage cost: ~$8/bulan (100GB EBS)" -ForegroundColor Cyan
Write-Host ""
