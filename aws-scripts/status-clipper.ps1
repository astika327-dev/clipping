# ================================================
# AI Video Clipper - Check Status Script
# ================================================
# Usage: .\status-clipper.ps1
# ================================================

# ========== CONFIGURATION ==========
$INSTANCE_ID = "i-XXXXXXXXXXXXX"  # <-- GANTI INI!
$REGION = "ap-southeast-1"        # <-- Sesuaikan region

# ========== SCRIPT ==========
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - Instance Status" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Instance ID is configured
if ($INSTANCE_ID -eq "i-XXXXXXXXXXXXX") {
    Write-Host "❌ ERROR: Instance ID belum dikonfigurasi!" -ForegroundColor Red
    exit 1
}

# Get instance details
$INSTANCE_DATA = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --region $REGION `
    --query "Reservations[0].Instances[0]" `
    --output json 2>$null | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to get instance info. Check your AWS credentials." -ForegroundColor Red
    exit 1
}

$STATUS = $INSTANCE_DATA.State.Name
$INSTANCE_TYPE = $INSTANCE_DATA.InstanceType
$PUBLIC_IP = $INSTANCE_DATA.PublicIpAddress
$LAUNCH_TIME = $INSTANCE_DATA.LaunchTime

# Display status with colors
Write-Host "📊 Instance ID    : $INSTANCE_ID" -ForegroundColor White
Write-Host "🖥️  Instance Type  : $INSTANCE_TYPE" -ForegroundColor White

if ($STATUS -eq "running") {
    Write-Host "✅ Status         : $STATUS" -ForegroundColor Green
    Write-Host "🌐 Public IP      : $PUBLIC_IP" -ForegroundColor Cyan
    Write-Host "⏰ Launch Time    : $LAUNCH_TIME" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 URL: http://$PUBLIC_IP" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  Instance is RUNNING - biaya compute aktif!" -ForegroundColor Yellow
    Write-Host "   Cost: ~$0.526/jam (g4dn.xlarge)" -ForegroundColor Yellow
} elseif ($STATUS -eq "stopped") {
    Write-Host "🛑 Status         : $STATUS" -ForegroundColor Red
    Write-Host ""
    Write-Host "💰 Instance STOPPED - tidak ada biaya compute." -ForegroundColor Green
    Write-Host "   Jalankan .\start-clipper.ps1 untuk memulai." -ForegroundColor Cyan
} else {
    Write-Host "⏳ Status         : $STATUS" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Instance sedang dalam proses $STATUS..." -ForegroundColor Yellow
}

Write-Host ""
