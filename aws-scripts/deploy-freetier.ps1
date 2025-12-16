# ================================================
# AI Video Clipper - AWS Free Tier Deployment (CPU Only)
# ================================================

param (
    [string]$Action = "deploy",
    [string]$Region = "ap-southeast-1",
    [string]$KeyPairName = "clipper-key-free"
)

# Ensure debug is off
Set-PSDebug -Off

Write-Host "🚀 STARTING DEPLOYMENT..." -ForegroundColor Cyan

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
        aws ec2 create-key-pair --key-name $KeyPairName --region $Region --query "KeyMaterial" --output text > "$HOME\.ssh\$KeyPairName.pem"
        Write-Host "✅ Key created"
    } else {
        Write-Host "✅ Key exists"
    }

    # 3. Security Group
    $sgName = "clipper-free-sg"
    $sgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=$sgName" --region $Region --query "SecurityGroups[0].GroupId" --output text 2>$null
    if ($sgId -eq "None" -or -not $sgId) {
        $sgId = aws ec2 create-security-group --group-name $sgName --description "Clipper Free SG" --region $Region --query "GroupId" --output text
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
echo "=== FREE TIER SETUP ==="
fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
apt-get update && apt-get install -y python3-pip python3-venv ffmpeg git nginx nodejs npm
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs
cd /home/ubuntu
git clone https://github.com/astika327-dev/clipping.git
chown -R ubuntu:ubuntu clipping
cd clipping/backend
python3 -m venv venv
source venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example .env
cat >> .env <<EOT
TRANSCRIPTION_BACKEND=faster-whisper
WHISPER_MODEL=base
FASTER_WHISPER_MODEL=base
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
ENABLE_DEEP_LEARNING_VIDEO=false
GROQ_API_ENABLED=true
USE_GPU_ACCELERATION=false
VIDEO_CODEC=libx264
EOT
mkdir -p uploads outputs
cd ../frontend && npm install && npm run build
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
        client_max_body_size 5G;
    }
}
NGINX
ln -sf /etc/nginx/sites-available/clipper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
"@
    $udEnc = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($userData))

    # 5. Launch - HARDCODED AMI
    Write-Host "🖥️ Launching Instance (ami-04c4b91fde394e924)..."
    
    # We use explicit arguments to avoid parsing issues
    $instanceId = aws ec2 run-instances `
        --image-id ami-04c4b91fde394e924 `
        --instance-type t3.micro `
        --key-name $KeyPairName `
        --security-group-ids $sgId `
        --user-data $udEnc `
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=AI-Clipper-Free}]" `
        --region $Region `
        --query "Instances[0].InstanceId" `
        --output text

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Launch Failed" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ INSTANCE LAUNCHED: $instanceId" -ForegroundColor Green
    aws ec2 wait instance-running --instance-ids $instanceId --region $Region
    $ip = aws ec2 describe-instances --instance-ids $instanceId --region $Region --query "Reservations[0].Instances[0].PublicIpAddress" --output text
    
    Write-Host "🌐 IP: http://$ip" -ForegroundColor Yellow
    Set-Content -Path "ssh-free.bat" -Value "ssh -i $HOME\.ssh\$KeyPairName.pem ubuntu@$ip"

} elseif ($Action -eq "status") {
    aws ec2 describe-instances --filters "Name=tag:Name,Values=AI-Clipper-Free" --region $Region --query "Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PublicIpAddress}" --output table
} elseif ($Action -eq "delete") {
    $ids = aws ec2 describe-instances --filters "Name=tag:Name,Values=AI-Clipper-Free" --region $Region --query "Reservations[].Instances[].InstanceId" --output text
    if ($ids) { aws ec2 terminate-instances --instance-ids $ids --region $Region; Write-Host "Deleted." }
}
