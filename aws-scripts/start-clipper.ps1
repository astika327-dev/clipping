# ================================================
# AI Video Clipper - Start Instance Script
# ================================================
# Usage: .\start-clipper.ps1
# ================================================

# ========== CONFIGURATION ==========
# Ganti dengan Instance ID kamu (dari AWS Console)
$INSTANCE_ID = "i-XXXXXXXXXXXXX"  # <-- GANTI INI!
$REGION = "ap-southeast-1"        # <-- Sesuaikan region

# ========== SCRIPT ==========
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - Starting AWS Instance" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Instance ID is configured
if ($INSTANCE_ID -eq "i-XXXXXXXXXXXXX") {
    Write-Host "❌ ERROR: Instance ID belum dikonfigurasi!" -ForegroundColor Red
    Write-Host "   Edit file ini dan ganti INSTANCE_ID dengan ID instance kamu." -ForegroundColor Yellow
    Write-Host "   Contoh: `$INSTANCE_ID = `"i-0abc123def456789`"" -ForegroundColor Yellow
    exit 1
}

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI tidak ditemukan!" -ForegroundColor Red
    Write-Host "   Install dengan: winget install Amazon.AWSCLI" -ForegroundColor Yellow
    exit 1
}

# Get current status
Write-Host "📊 Checking current status..." -ForegroundColor Yellow
$STATUS = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --region $REGION `
    --query "Reservations[0].Instances[0].State.Name" `
    --output text 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to get instance status. Check your AWS credentials." -ForegroundColor Red
    exit 1
}

if ($STATUS -eq "running") {
    Write-Host "✅ Instance sudah running!" -ForegroundColor Green
    $PUBLIC_IP = aws ec2 describe-instances `
        --instance-ids $INSTANCE_ID `
        --region $REGION `
        --query "Reservations[0].Instances[0].PublicIpAddress" `
        --output text
    Write-Host "🌐 URL: http://$PUBLIC_IP" -ForegroundColor Cyan
    Start-Process "http://$PUBLIC_IP"
    exit 0
}

# Start instance
Write-Host "🚀 Starting instance..." -ForegroundColor Cyan
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start instance!" -ForegroundColor Red
    exit 1
}

# Wait for running
Write-Host "⏳ Waiting for instance to be ready (1-2 minutes)..." -ForegroundColor Yellow
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
Write-Host "⏳ Waiting for services to initialize (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   ✅ AI Video Clipper is READY!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access URL: http://$PUBLIC_IP" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  PENTING: Jangan lupa jalankan .\stop-clipper.ps1" -ForegroundColor Yellow
Write-Host "   setelah selesai untuk menghindari biaya!" -ForegroundColor Yellow
Write-Host ""

# Open browser
Start-Process "http://$PUBLIC_IP"
