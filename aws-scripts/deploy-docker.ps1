# ================================================
# AI Video Clipper - Docker AWS Deployment
# ================================================
# Deploy EC2 GPU instance dengan Docker
# ================================================

param (
    [string]$Action = "deploy",  # deploy, status, update, delete
    [string]$InstanceType = "g4dn.xlarge",
    [string]$Region = "ap-southeast-1",
    [string]$KeyPairName = "clipper-key",
    [string]$GitHubToken = ""  # PAT untuk pull dari GHCR
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - Docker AWS Deploy" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ========== CHECK AWS CLI ==========
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI tidak ditemukan!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install dengan:" -ForegroundColor Yellow
    Write-Host "  winget install Amazon.AWSCLI" -ForegroundColor White
    exit 1
}

# ========== CHECK CREDENTIALS ==========
$IDENTITY = aws sts get-caller-identity 2>$null | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ AWS credentials belum dikonfigurasi!" -ForegroundColor Red
    Write-Host "   Jalankan: aws configure" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ AWS Account: $($IDENTITY.Account)" -ForegroundColor Green
Write-Host "   Region: $Region" -ForegroundColor White
Write-Host ""

# ========== DEPLOY ACTION ==========
if ($Action -eq "deploy") {
    Write-Host "🚀 Deploying AI Video Clipper with Docker..." -ForegroundColor Cyan
    Write-Host "   Instance Type: $InstanceType" -ForegroundColor White
    Write-Host ""

    # Check GitHub Token
    if ([string]::IsNullOrEmpty($GitHubToken)) {
        Write-Host "⚠️  GitHub Token tidak disediakan." -ForegroundColor Yellow
        Write-Host "   Image harus di-pull manual setelah instance ready." -ForegroundColor Yellow
        Write-Host ""
        $GitHubToken = ""
    }

    # Step 1: Check/Create Key Pair
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

    # Step 2: Check/Create Security Group
    Write-Host ""
    Write-Host "🔒 Step 2: Checking Security Group..." -ForegroundColor Yellow
    
    $sgName = "clipper-docker-sg"
    $sgId = aws ec2 describe-security-groups `
        --filters "Name=group-name,Values=$sgName" `
        --region $Region `
        --query "SecurityGroups[0].GroupId" `
        --output text 2>$null

    if ($sgId -eq "None" -or $null -eq $sgId -or $sgId -eq "") {
        Write-Host "   Creating security group..." -ForegroundColor White
        
        $sgId = aws ec2 create-security-group `
            --group-name $sgName `
            --description "AI Video Clipper Docker Security Group" `
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

    # Step 4: Prepare User Data Script
    Write-Host ""
    Write-Host "📝 Step 4: Preparing Docker setup script..." -ForegroundColor Yellow
    
    # Read the user data script
    $scriptPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "userdata-docker.sh"
    if (Test-Path $scriptPath) {
        $userData = Get-Content $scriptPath -Raw
    } else {
        Write-Host "   ❌ userdata-docker.sh not found!" -ForegroundColor Red
        exit 1
    }

    # Inject GitHub token if provided
    if (-not [string]::IsNullOrEmpty($GitHubToken)) {
        $userData = $userData -replace 'GITHUB_TOKEN="\$\{GITHUB_TOKEN:-\}"', "GITHUB_TOKEN=`"$GitHubToken`""
    }

    $userDataBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($userData))

    # Step 5: Launch EC2 Instance
    Write-Host ""
    Write-Host "🖥️ Step 5: Launching EC2 GPU Instance with Docker..." -ForegroundColor Yellow
    Write-Host "   This may take a few minutes..." -ForegroundColor White
    
    $instanceId = aws ec2 run-instances `
        --image-id $amiId `
        --instance-type $InstanceType `
        --key-name $KeyPairName `
        --security-group-ids $sgId `
        --user-data $userDataBase64 `
        --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' `
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=AI-Video-Clipper-Docker}]" `
        --region $Region `
        --query "Instances[0].InstanceId" `
        --output text

    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ❌ Failed to launch instance" -ForegroundColor Red
        exit 1
    }

    Write-Host "   ✅ Instance launched: $instanceId" -ForegroundColor Green

    # Wait for instance
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
    Write-Host "   ✅ DOCKER DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Instance Details:" -ForegroundColor Cyan
    Write-Host "   ID:   $instanceId" -ForegroundColor White
    Write-Host "   IP:   $publicIp" -ForegroundColor White
    Write-Host "   Type: $InstanceType" -ForegroundColor White
    Write-Host ""
    Write-Host "⏳ Setup sedang berjalan (~5-7 menit)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "SSH ke instance:" -ForegroundColor Cyan
    Write-Host "   ssh -i $HOME\.ssh\$KeyPairName.pem ubuntu@$publicIp" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Cek progress setup:" -ForegroundColor Cyan
    Write-Host "   tail -f /var/log/user-data.log" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Setelah selesai, akses di:" -ForegroundColor Cyan
    Write-Host "   http://$publicIp" -ForegroundColor Green
    Write-Host ""
    
    if ([string]::IsNullOrEmpty($GitHubToken)) {
        Write-Host "⚠️  Untuk pull image, SSH dan jalankan:" -ForegroundColor Yellow
        Write-Host '   echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u astika327-dev --password-stdin' -ForegroundColor Gray
        Write-Host "   cd /home/ubuntu/clipper && docker compose up -d" -ForegroundColor Gray
        Write-Host ""
    }
    
    Write-Host "💰 PENTING: Stop instance saat tidak digunakan!" -ForegroundColor Yellow
    Write-Host ""

    # Save instance ID to a file for other scripts
    $instanceFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "docker-instance.txt"
    "$instanceId,$Region,$publicIp" | Out-File $instanceFile -Encoding utf8

} elseif ($Action -eq "status") {
    Write-Host "📊 Checking AI Video Clipper Docker instances..." -ForegroundColor Cyan
    
    aws ec2 describe-instances `
        --filters "Name=tag:Name,Values=AI-Video-Clipper-Docker" `
        --region $Region `
        --query "Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PublicIpAddress,Type:InstanceType}" `
        --output table

} elseif ($Action -eq "update") {
    Write-Host "🔄 Updating Docker image on running instance..." -ForegroundColor Cyan
    
    $instanceFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "docker-instance.txt"
    if (Test-Path $instanceFile) {
        $instanceData = Get-Content $instanceFile
        $parts = $instanceData.Split(",")
        $instanceId = $parts[0]
        
        # Get current IP
        $publicIp = aws ec2 describe-instances `
            --instance-ids $instanceId `
            --region $Region `
            --query "Reservations[0].Instances[0].PublicIpAddress" `
            --output text

        Write-Host "   Instance: $instanceId" -ForegroundColor White
        Write-Host "   IP: $publicIp" -ForegroundColor White
        Write-Host ""
        Write-Host "SSH dan jalankan:" -ForegroundColor Yellow
        Write-Host "   cd /home/ubuntu/clipper && ./update.sh" -ForegroundColor Gray
    } else {
        Write-Host "❌ No instance file found. Deploy first." -ForegroundColor Red
    }

} elseif ($Action -eq "delete") {
    Write-Host "🗑️ Finding AI Video Clipper Docker instances to delete..." -ForegroundColor Red
    
    $instances = aws ec2 describe-instances `
        --filters "Name=tag:Name,Values=AI-Video-Clipper-Docker" `
        --region $Region `
        --query "Reservations[].Instances[].InstanceId" `
        --output text

    if ($instances) {
        Write-Host "Found instances: $instances" -ForegroundColor Yellow
        $confirm = Read-Host "Delete these instances? (y/N)"
        
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            aws ec2 terminate-instances --instance-ids $instances --region $Region
            Write-Host "✅ Instances terminated" -ForegroundColor Green
            
            # Remove instance file
            $instanceFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "docker-instance.txt"
            if (Test-Path $instanceFile) {
                Remove-Item $instanceFile
            }
        }
    } else {
        Write-Host "No instances found." -ForegroundColor Yellow
    }
}
