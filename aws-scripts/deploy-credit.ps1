# ================================================
# AI Video Clipper - AWS Credit Deployment (High Performance CPU)
# ================================================
# Menggunakan saldo kredit $100
# Instance: t3.xlarge (4 vCPU, 16GB RAM) - ~$0.17/jam
# Storage: 100GB - ~$8/bulan
# ================================================

param (
    [string]$Action = "deploy",
    [string]$Region = "ap-southeast-1",
    [string]$KeyPairName = "clipper-key-credit"
)

# Debug trace off
Set-PSDebug -Off

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Clipper - Credit Mode ($100 High Perf)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Instance: t3.xlarge (16GB RAM)" -ForegroundColor White
Write-Host "   Storage:  100 GB" -ForegroundColor White
Write-Host ""

# 1. Check AWS
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI missing." -ForegroundColor Red; exit 1
}

$ids = aws sts get-caller-identity --output json | ConvertFrom-Json
if (-not $ids) { Write-Host "❌ AWS not configured."; exit 1 }
Write-Host "✅ Account: $($ids.Account)"

if ($Action -eq "deploy") {
    # 2. Key Pair
    $keyCheck = aws ec2 describe-key-pairs --key-names $KeyPairName --region $Region 2>$null
    if (-not $keyCheck) {
        $keyPath = "$env:USERPROFILE\.ssh\$KeyPairName.pem"
        aws ec2 create-key-pair --key-name $KeyPairName --region $Region --query "KeyMaterial" --output text > $keyPath
        Write-Host "✅ Key created: $keyPath"
    } else {
        Write-Host "✅ Key exists"
    }

    # 3. Security Group
    $sgName = "clipper-credit-sg"
    $sgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=$sgName" --region $Region --query "SecurityGroups[0].GroupId" --output text 2>$null
    if ($sgId -eq "None" -or -not $sgId) {
        $sgId = aws ec2 create-security-group --group-name $sgName --description "Clipper Credit SG" --region $Region --query "GroupId" --output text
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $Region >$null
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $Region >$null
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 5000 --cidr 0.0.0.0/0 --region $Region >$null
        Write-Host "✅ SG created: $sgId"
    } else {
        Write-Host "✅ SG exists: $sgId"
    }

    # 4. User Data
    $userData = @"
#!/bin/bash
exec > >(tee /var/log/user-data.log) 2>&1
echo "=== CREDIT TIER SETUP (HIGH PERF) ==="

# 100GB Disk is enough, but 4GB swap is still good for stability
fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

apt-get update && apt-get install -y python3-pip python3-venv ffmpeg git nginx nodejs npm

# Install NodeJS 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs

cd /home/ubuntu
git clone https://github.com/astika327-dev/clipping.git
chown -R ubuntu:ubuntu clipping
cd clipping/backend

# Virtual Env
python3 -m venv venv
source venv/bin/activate

# Install Full PyTorch (CPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install All Requirements
pip install -r requirements.txt

# Config .env
cp .env.example .env
cat >> .env <<EOT

# === CREDIT TIER OVERRIDES ===
TRANSCRIPTION_BACKEND=faster-whisper
WHISPER_MODEL=medium
FASTER_WHISPER_MODEL=medium
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
ENABLE_DEEP_LEARNING_VIDEO=true
YOLO_MODEL_SIZE=n
GROQ_API_ENABLED=true
USE_GPU_ACCELERATION=false
VIDEO_CODEC=libx264
NVENC_PRESET=faster
PROCESSING_CONCURRENCY=2
EOT

mkdir -p uploads outputs

# Build Frontend
cd ../frontend && npm install && npm run build

# Nginx & Systemd
cat > /etc/systemd/system/clipper-backend.service << 'EOF'
[Unit]
Description=Backend
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/clipping/backend
Environment="PATH=/home/ubuntu/clipping/venv/bin:/usr/bin"
ExecStart=/home/ubuntu/clipping/venv/bin/python app.py --production --port 5000
Restart=always
[Install]
WantedBy=multi-user.target
EOF

systemctl enable clipper-backend && systemctl start clipper-backend

cat > /etc/nginx/sites-available/clipper << 'NGINX'
server {
    listen 80;
    location / { root /home/ubuntu/clipping/frontend/dist; try_files \$uri \$uri/ /index.html; }
    location ~ ^/(upload|process|status|download|clips|storage|system|health|youtube|api) {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        client_max_body_size 10G;
        proxy_read_timeout 900;
        send_timeout 900;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/clipper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
"@
    $udEnc = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($userData))

    # 5. Launch - ROBUST JSON CONFIG METHOD (Object based)
    Write-Host "🖥️ Launching t3.xlarge (16GB RAM, 100GB Disk)..."
    
    $TargetAmiId = "ami-04c4b91fde394e924"

    # Define simple object for JSON
    $launchConfig = @{
        ImageId = $TargetAmiId
        InstanceType = "t3.xlarge"
        KeyName = $KeyPairName
        SecurityGroupIds = @($sgId)
        UserData = $udEnc
        BlockDeviceMappings = @(
            @{
                DeviceName = "/dev/sda1"
                Ebs = @{
                    VolumeSize = 100
                    VolumeType = "gp3"
                }
            }
        )
        TagSpecifications = @(
            @{
                ResourceType = "instance"
                Tags = @(
                    @{ Key = "Name"; Value = "AI-Clipper-Credit" }
                )
            }
        )
    }

    $jsonConfigFile = "$PSScriptRoot\launch-config.json"
    $launchConfig | ConvertTo-Json -Depth 10 | Set-Content -Path $jsonConfigFile -Encoding Ascii

    try {
        $instanceId = aws ec2 run-instances --cli-input-json "file://$jsonConfigFile" --region $Region --query "Instances[0].InstanceId" --output text
    } finally {
        if (Test-Path $jsonConfigFile) { Remove-Item $jsonConfigFile }
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Launch Failed" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ INSTANCE LAUNCHED: $instanceId" -ForegroundColor Green
    Write-Host "⏳ Waiting for initialization..."
    aws ec2 wait instance-running --instance-ids $instanceId --region $Region
    $ip = aws ec2 describe-instances --instance-ids $instanceId --region $Region --query "Reservations[0].Instances[0].PublicIpAddress" --output text
    
    Write-Host "🌐 IP: http://$ip" -ForegroundColor Yellow
    Set-Content -Path "ssh-credit.bat" -Value "ssh -i ""$env:USERPROFILE\.ssh\$KeyPairName.pem"" ubuntu@$ip"
    Write-Host "👉 Use '.\ssh-credit.bat' to login."
    
    # Check for Cookies
    $cookiesPath = Join-Path $PSScriptRoot "..\backend\youtube_cookies.txt"
    if (Test-Path $cookiesPath) {
        Write-Host "🍪 Cookies found! Prepare upload..."
        $uploadCmd = "scp -i ""$env:USERPROFILE\.ssh\$KeyPairName.pem"" -o StrictHostKeyChecking=no ""$cookiesPath"" ubuntu@${ip}:~/clipping/backend/youtube_cookies.txt"
        Set-Content -Path "upload-cookies.bat" -Value $uploadCmd
        Write-Host "   Run '.\upload-cookies.bat' AFTER setup completes (~5 mins) to enable YouTube cookies." -ForegroundColor Yellow
    }

} elseif ($Action -eq "status") {
    aws ec2 describe-instances --filters "Name=tag:Name,Values=AI-Clipper-Credit" --region $Region --query "Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PublicIpAddress,Type:InstanceType}" --output table
} elseif ($Action -eq "delete") {
    $ids = aws ec2 describe-instances --filters "Name=tag:Name,Values=AI-Clipper-Credit" --region $Region --query "Reservations[].Instances[].InstanceId" --output text
    if ($ids) { aws ec2 terminate-instances --instance-ids $ids --region $Region; Write-Host "Deleted." }
}
