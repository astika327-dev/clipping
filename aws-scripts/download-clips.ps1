# ================================================
# AI Video Clipper - Download Clips from AWS
# ================================================
# Usage: .\download-clips.ps1
# Downloads all clips from running instance to local PC
# ================================================

# ========== CONFIGURATION ==========
$INSTANCE_ID = "i-XXXXXXXXXXXXX"  # <-- GANTI INI!
$REGION = "ap-southeast-1"
$KEY_FILE = "$HOME\.ssh\your-key.pem"  # <-- Path ke SSH key
$LOCAL_DOWNLOAD_PATH = "$HOME\Downloads\clipper-outputs"

# ========== SCRIPT ==========
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - Download Clips" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Instance ID is configured
if ($INSTANCE_ID -eq "i-XXXXXXXXXXXXX") {
    Write-Host "❌ ERROR: Instance ID belum dikonfigurasi!" -ForegroundColor Red
    exit 1
}

# Get public IP
$PUBLIC_IP = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --region $REGION `
    --query "Reservations[0].Instances[0].PublicIpAddress" `
    --output text 2>$null

if (-not $PUBLIC_IP -or $PUBLIC_IP -eq "None") {
    Write-Host "❌ Instance tidak running atau tidak ada Public IP." -ForegroundColor Red
    Write-Host "   Jalankan .\start-clipper.ps1 terlebih dahulu." -ForegroundColor Yellow
    exit 1
}

Write-Host "📡 Instance IP: $PUBLIC_IP" -ForegroundColor Cyan
Write-Host "📂 Download ke: $LOCAL_DOWNLOAD_PATH" -ForegroundColor White
Write-Host ""

# Create download directory
if (-not (Test-Path $LOCAL_DOWNLOAD_PATH)) {
    New-Item -ItemType Directory -Path $LOCAL_DOWNLOAD_PATH -Force | Out-Null
}

# Download using SCP
Write-Host "📥 Downloading clips..." -ForegroundColor Yellow

# Check if key file exists
if (-not (Test-Path $KEY_FILE)) {
    Write-Host "⚠️  SSH key not found at: $KEY_FILE" -ForegroundColor Yellow
    Write-Host "   Using password authentication..." -ForegroundColor Yellow
    
    # Download without key
    scp -r "ubuntu@${PUBLIC_IP}:/home/ubuntu/clipping/backend/outputs/*" "$LOCAL_DOWNLOAD_PATH/"
} else {
    # Download with key
    scp -i $KEY_FILE -r "ubuntu@${PUBLIC_IP}:/home/ubuntu/clipping/backend/outputs/*" "$LOCAL_DOWNLOAD_PATH/"
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Download complete!" -ForegroundColor Green
    Write-Host "📂 Files saved to: $LOCAL_DOWNLOAD_PATH" -ForegroundColor Cyan
    
    # Open folder
    explorer $LOCAL_DOWNLOAD_PATH
} else {
    Write-Host "❌ Download failed. Check SSH connection." -ForegroundColor Red
}

Write-Host ""
