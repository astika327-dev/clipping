# Deploy ke Sydney (ap-southeast-2)
$ErrorActionPreference = "Stop"
$Region = "ap-southeast-2"
$InstanceType = "g4dn.xlarge"
$KeyPairName = "clipper-key"

Write-Host "🚀 Deploying AI Video Clipper ke Sydney..." -ForegroundColor Cyan

# 1. Cek/buat key pair
Write-Host "🔑 Checking key pair..." -ForegroundColor Yellow
$keyCheck = aws ec2 describe-key-pairs --key-names $KeyPairName --region $Region 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Creating key pair in Sydney..." -ForegroundColor White
    $keyPath = "$HOME\.ssh\clipper-key-sydney.pem"
    aws ec2 create-key-pair --key-name $KeyPairName --region $Region --query "KeyMaterial" --output text > $keyPath
    Write-Host "   ✅ Key saved: $keyPath" -ForegroundColor Green
} else {
    Write-Host "   ✅ Key pair exists" -ForegroundColor Green
}

# 2. Cek/buat security group
Write-Host "🔒 Checking security group..." -ForegroundColor Yellow
$sgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=clipper-security-group" --region $Region --query "SecurityGroups[0].GroupId" --output text 2>&1

if ($sgId -eq "None" -or $sgId -match "error") {
    Write-Host "   Creating security group..." -ForegroundColor White
    $sgResult = aws ec2 create-security-group --group-name clipper-security-group --description "AI Video Clipper" --region $Region --output json | ConvertFrom-Json
    $sgId = $sgResult.GroupId
    
    # Add rules
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $Region 2>&1 | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $Region 2>&1 | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $Region 2>&1 | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 5000 --cidr 0.0.0.0/0 --region $Region 2>&1 | Out-Null
    Write-Host "   ✅ Security group created: $sgId" -ForegroundColor Green
} else {
    Write-Host "   ✅ Security group exists: $sgId" -ForegroundColor Green
}

# 3. Get Ubuntu AMI
Write-Host "🖼️ Getting Ubuntu AMI..." -ForegroundColor Yellow
$amiId = aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" --query "Images[-1].ImageId" --region $Region --output text
Write-Host "   ✅ AMI: $amiId" -ForegroundColor Green

# 4. Read user data
Write-Host "📝 Preparing user data..." -ForegroundColor Yellow
$userDataContent = Get-Content -Path ".\aws-scripts\userdata.sh" -Raw
$userDataBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($userDataContent))
Write-Host "   ✅ User data prepared" -ForegroundColor Green

# 5. Launch instance
Write-Host "🖥️ Launching g4dn.xlarge instance..." -ForegroundColor Yellow
$launchResult = aws ec2 run-instances `
    --image-id $amiId `
    --instance-type $InstanceType `
    --key-name $KeyPairName `
    --security-group-ids $sgId `
    --user-data $userDataBase64 `
    --block-device-mappings file://aws-scripts/block-device.json `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=AI-Video-Clipper}]" `
    --region $Region `
    --output json | ConvertFrom-Json

$instanceId = $launchResult.Instances[0].InstanceId
Write-Host "   ✅ Instance launched: $instanceId" -ForegroundColor Green

# 6. Wait for running
Write-Host "⏳ Waiting for instance to start..." -ForegroundColor Yellow
aws ec2 wait instance-running --instance-ids $instanceId --region $Region
Write-Host "   ✅ Instance is running!" -ForegroundColor Green

# 7. Get public IP
$publicIp = aws ec2 describe-instances --instance-ids $instanceId --region $Region --query "Reservations[0].Instances[0].PublicIpAddress" --output text

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   ✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Instance Details:" -ForegroundColor Cyan
Write-Host "   ID:     $instanceId"
Write-Host "   IP:     $publicIp"
Write-Host "   Type:   $InstanceType"
Write-Host "   Region: $Region (Sydney)"
Write-Host ""
Write-Host "⏳ Setup sedang berjalan (~10-15 menit)" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔗 SSH Command:" -ForegroundColor Cyan
Write-Host "   ssh -i $HOME\.ssh\clipper-key-sydney.pem ubuntu@$publicIp"
Write-Host ""
Write-Host "🌐 Akses aplikasi setelah setup selesai:" -ForegroundColor Cyan
Write-Host "   http://$publicIp" -ForegroundColor Green
Write-Host ""
Write-Host "💰 BUDGET INFO ($119 Credit):" -ForegroundColor Yellow
Write-Host "   g4dn.xlarge = ~$0.526/jam"
Write-Host "   Storage 50GB = ~$4/bulan"
Write-Host "   Est. ~200 jam compute tersedia"
Write-Host ""
Write-Host "⚠️ JANGAN LUPA STOP instance saat tidak digunakan!" -ForegroundColor Red
Write-Host "   aws ec2 stop-instances --instance-ids $instanceId --region $Region"
