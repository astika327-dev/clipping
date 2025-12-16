# ================================================
# AI Video Clipper - Full AWS Deployment via PowerShell
# ================================================
# Script ini deploy EC2 GPU instance langsung dari PowerShell
# Hanya perlu 1x setup AWS credentials
# ================================================

param (
    [string]$Action = "deploy",  # deploy, status, delete
    [string]$InstanceType = "g4dn.xlarge",
    [string]$Region = "ap-southeast-1",
    [string]$KeyPairName = "clipper-key"
)

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - AWS PowerShell Deploy" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ========== CHECK AWS CLI ==========
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI tidak ditemukan!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install dengan:" -ForegroundColor Yellow
    Write-Host "  winget install Amazon.AWSCLI" -ForegroundColor White
    Write-Host ""
    Write-Host "Setelah install, restart PowerShell dan jalankan:" -ForegroundColor Yellow
    Write-Host "  aws configure" -ForegroundColor White
    Write-Host ""
    Write-Host "Kamu akan butuh Access Key dari AWS Console:" -ForegroundColor Yellow
    Write-Host "  https://console.aws.amazon.com/iam/home#/security_credentials" -ForegroundColor Cyan
    exit 1
}

# ========== CHECK CREDENTIALS ==========
$IDENTITY = aws sts get-caller-identity 2>$null | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ AWS credentials belum dikonfigurasi!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Langkah-langkah:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Buka AWS Console untuk buat Access Key:" -ForegroundColor White
    Write-Host "   https://console.aws.amazon.com/iam/home#/security_credentials" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Klik 'Create access key'" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Jalankan command ini dan masukkan credentials:" -ForegroundColor White
    Write-Host "   aws configure" -ForegroundColor Green
    Write-Host ""
    Write-Host "   - Access Key ID: (dari step 2)" -ForegroundColor Gray
    Write-Host "   - Secret Access Key: (dari step 2)" -ForegroundColor Gray
    Write-Host "   - Region: ap-southeast-1" -ForegroundColor Gray
    Write-Host "   - Output format: json" -ForegroundColor Gray
    Write-Host ""
    
    $configure = Read-Host "Jalankan 'aws configure' sekarang? (y/N)"
    if ($configure -eq "y" -or $configure -eq "Y") {
        aws configure
        
        # Re-check
        $IDENTITY = aws sts get-caller-identity 2>$null | ConvertFrom-Json
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Configuration failed. Coba lagi." -ForegroundColor Red
            exit 1
        }
    } else {
        exit 1
    }
}

Write-Host "✅ AWS Account: $($IDENTITY.Account)" -ForegroundColor Green
Write-Host "   Region: $Region" -ForegroundColor White
Write-Host ""

# ========== DEPLOY ACTION ==========
if ($Action -eq "deploy") {
    Write-Host "🚀 Deploying AI Video Clipper to AWS..." -ForegroundColor Cyan
    Write-Host "   Instance Type: $InstanceType" -ForegroundColor White
    Write-Host ""

    # Step 1: Create Key Pair (if not exists)
    Write-Host "🔑 Step 1: Checking Key Pair..." -ForegroundColor Yellow
    $keyExists = aws ec2 describe-key-pairs --key-names $KeyPairName --region $Region 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Creating new key pair: $KeyPairName" -ForegroundColor White
        
        $keyPath = "$HOME\.ssh\$KeyPairName.pem"
        aws ec2 create-key-pair `
            --key-name $KeyPairName `
            --region $Region `
            --query "KeyMaterial" `
            --output text > $keyPath
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Key pair saved to: $keyPath" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Failed to create key pair" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "   ✅ Key pair exists: $KeyPairName" -ForegroundColor Green
    }

    # Step 2: Create Security Group
    Write-Host ""
    Write-Host "🔒 Step 2: Checking Security Group..." -ForegroundColor Yellow
    
    $sgName = "clipper-security-group"
    $sgId = aws ec2 describe-security-groups `
        --filters "Name=group-name,Values=$sgName" `
        --region $Region `
        --query "SecurityGroups[0].GroupId" `
        --output text 2>$null

    if ($sgId -eq "None" -or $null -eq $sgId) {
        Write-Host "   Creating security group..." -ForegroundColor White
        
        $sgId = aws ec2 create-security-group `
            --group-name $sgName `
            --description "AI Video Clipper Security Group" `
            --region $Region `
            --query "GroupId" `
            --output text

        # Add rules
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $Region 2>$null
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $Region 2>$null
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $Region 2>$null
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 5000 --cidr 0.0.0.0/0 --region $Region 2>$null
        
        Write-Host "   ✅ Security Group created: $sgId" -ForegroundColor Green
    } else {
        Write-Host "   ✅ Security Group exists: $sgId" -ForegroundColor Green
    }

    # Step 3: Get Ubuntu AMI
    Write-Host ""
    Write-Host "🖼️ Step 3: Finding Ubuntu 22.04 AMI..." -ForegroundColor Yellow
    
    $amiId = aws ec2 describe-images `
        --owners 099720109477 `
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" `
        --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" `
        --region $Region `
        --output text

    Write-Host "   ✅ AMI: $amiId" -ForegroundColor Green

    # Step 4: Create User Data script
    Write-Host ""
    Write-Host "📝 Step 4: Preparing setup script..." -ForegroundColor Yellow
    
    $userData = @"
#!/bin/bash
exec > >(tee /var/log/user-data.log) 2>&1
echo "=== AI Video Clipper Setup ==="

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y python3 python3-pip python3-venv ffmpeg git curl wget nginx

# Install NVIDIA drivers
apt-get install -y nvidia-driver-535 nvidia-cuda-toolkit

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Clone repository
cd /home/ubuntu
git clone https://github.com/astika327-dev/clipping.git
chown -R ubuntu:ubuntu clipping

# Setup Python
cd clipping
python3 -m venv venv
source venv/bin/activate

cd backend
pip install --upgrade pip
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

cp .env.example .env
mkdir -p uploads outputs

# Build frontend
cd ../frontend
npm install
npm run build

# Setup systemd service
cat > /etc/systemd/system/clipper-backend.service << 'EOF'
[Unit]
Description=AI Video Clipper Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/clipping/backend
Environment="PATH=/home/ubuntu/clipping/venv/bin:/usr/bin"
ExecStart=/home/ubuntu/clipping/venv/bin/python app.py --production --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable clipper-backend
systemctl start clipper-backend

# Configure Nginx
cat > /etc/nginx/sites-available/clipper << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        root /home/ubuntu/clipping/frontend/dist;
        try_files `$uri `$uri/ /index.html;
    }
    
    location ~ ^/(upload|process|status|download|clips|storage|system|health|youtube|api) {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host `$host;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        client_max_body_size 5G;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/clipper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "=== Setup Complete ==="
"@

    # Encode to base64
    $userDataBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($userData))

    # Step 5: Launch EC2 Instance
    Write-Host ""
    Write-Host "🖥️ Step 5: Launching EC2 GPU Instance..." -ForegroundColor Yellow
    Write-Host "   This may take a few minutes..." -ForegroundColor White
    
    $instanceId = aws ec2 run-instances `
        --image-id $amiId `
        --instance-type $InstanceType `
        --key-name $KeyPairName `
        --security-group-ids $sgId `
        --user-data $userDataBase64 `
        --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' `
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=AI-Video-Clipper}]" `
        --region $Region `
        --query "Instances[0].InstanceId" `
        --output text

    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ❌ Failed to launch instance" -ForegroundColor Red
        exit 1
    }

    Write-Host "   ✅ Instance launched: $instanceId" -ForegroundColor Green

    # Wait for instance to be running
    Write-Host ""
    Write-Host "⏳ Waiting for instance to start..." -ForegroundColor Yellow
    aws ec2 wait instance-running --instance-ids $instanceId --region $Region

    # Get public IP
    $publicIp = aws ec2 describe-instances `
        --instance-ids $instanceId `
        --region $Region `
        --query "Reservations[0].Instances[0].PublicIpAddress" `
        --output text

    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "   ✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Instance Details:" -ForegroundColor Cyan
    Write-Host "   ID:   $instanceId" -ForegroundColor White
    Write-Host "   IP:   $publicIp" -ForegroundColor White
    Write-Host "   Type: $InstanceType" -ForegroundColor White
    Write-Host ""
    Write-Host "⏳ Setup sedang berjalan di server (~5-10 menit)" -ForegroundColor Yellow
    Write-Host "   Cek status setup dengan SSH:" -ForegroundColor White
    Write-Host "   ssh -i $HOME\.ssh\$KeyPairName.pem ubuntu@$publicIp" -ForegroundColor Gray
    Write-Host "   tail -f /var/log/user-data.log" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🌐 Setelah selesai, akses di:" -ForegroundColor Cyan
    Write-Host "   http://$publicIp" -ForegroundColor Green
    Write-Host ""
    Write-Host "💰 PENTING: Jangan lupa STOP instance saat tidak digunakan!" -ForegroundColor Yellow
    Write-Host ""

    # Save instance ID to scripts
    $scriptsPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    if (Test-Path "$scriptsPath\start-clipper.ps1") {
        $content = Get-Content "$scriptsPath\start-clipper.ps1" -Raw
        $content = $content -replace 'i-XXXXXXXXXXXXX', $instanceId
        $content = $content -replace 'ap-southeast-1', $Region
        Set-Content "$scriptsPath\start-clipper.ps1" $content

        $content = Get-Content "$scriptsPath\stop-clipper.ps1" -Raw
        $content = $content -replace 'i-XXXXXXXXXXXXX', $instanceId
        $content = $content -replace 'ap-southeast-1', $Region
        Set-Content "$scriptsPath\stop-clipper.ps1" $content

        $content = Get-Content "$scriptsPath\status-clipper.ps1" -Raw
        $content = $content -replace 'i-XXXXXXXXXXXXX', $instanceId
        $content = $content -replace 'ap-southeast-1', $Region
        Set-Content "$scriptsPath\status-clipper.ps1" $content

        Write-Host "✅ Scripts updated dengan Instance ID" -ForegroundColor Green
    }

} elseif ($Action -eq "status") {
    # Status action - check existing instances
    Write-Host "📊 Checking AI Video Clipper instances..." -ForegroundColor Cyan
    
    aws ec2 describe-instances `
        --filters "Name=tag:Name,Values=AI-Video-Clipper" `
        --region $Region `
        --query "Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PublicIpAddress,Type:InstanceType}" `
        --output table

} elseif ($Action -eq "delete") {
    # Delete action
    Write-Host "🗑️ Finding AI Video Clipper instances to delete..." -ForegroundColor Red
    
    $instances = aws ec2 describe-instances `
        --filters "Name=tag:Name,Values=AI-Video-Clipper" `
        --region $Region `
        --query "Reservations[].Instances[].InstanceId" `
        --output text

    if ($instances) {
        Write-Host "Found instances: $instances" -ForegroundColor Yellow
        $confirm = Read-Host "Delete these instances? (y/N)"
        
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            aws ec2 terminate-instances --instance-ids $instances --region $Region
            Write-Host "✅ Instances terminated" -ForegroundColor Green
        }
    } else {
        Write-Host "No instances found." -ForegroundColor Yellow
    }
}
