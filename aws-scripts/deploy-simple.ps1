# Simple AWS Deploy Script - Fixed Version
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - AWS Deploy" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$Region = "ap-southeast-1"
$InstanceType = "g4dn.xlarge"
$KeyPairName = "clipper-key"

# Step 1: Create Key Pair
Write-Host "[1/4] Creating Key Pair..." -ForegroundColor Yellow
$keyPath = "$HOME\.ssh"
if (-not (Test-Path $keyPath)) { 
    New-Item -ItemType Directory -Path $keyPath -Force | Out-Null 
}

$keyCheck = aws ec2 describe-key-pairs --key-names $KeyPairName --region $Region 2>&1
if ($LASTEXITCODE -ne 0) {
    $keyMaterial = aws ec2 create-key-pair --key-name $KeyPairName --region $Region --query "KeyMaterial" --output text
    $keyMaterial | Out-File -FilePath "$keyPath\$KeyPairName.pem" -Encoding ASCII -NoNewline
    Write-Host "   Key pair created: $keyPath\$KeyPairName.pem" -ForegroundColor Green
} else {
    Write-Host "   Key pair exists" -ForegroundColor Green
}

# Step 2: Create Security Group
Write-Host ""
Write-Host "[2/4] Creating Security Group..." -ForegroundColor Yellow
$sgName = "clipper-sg"

$vpcId = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region $Region --query "Vpcs[0].VpcId" --output text 2>&1

$sgCheck = aws ec2 describe-security-groups --filters "Name=group-name,Values=$sgName" --region $Region --query "SecurityGroups[0].GroupId" --output text 2>&1

if ($sgCheck -eq "None" -or $LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($sgCheck)) {
    $sgId = aws ec2 create-security-group --group-name $sgName --description "AI-Video-Clipper" --vpc-id $vpcId --region $Region --query "GroupId" --output text
    
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $Region 2>&1 | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $Region 2>&1 | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 5000 --cidr 0.0.0.0/0 --region $Region 2>&1 | Out-Null
    
    Write-Host "   Security Group created: $sgId" -ForegroundColor Green
} else {
    $sgId = $sgCheck
    Write-Host "   Security Group exists: $sgId" -ForegroundColor Green
}

# Step 3: Find AMI
Write-Host ""
Write-Host "[3/4] Finding Ubuntu AMI..." -ForegroundColor Yellow
$amiId = aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-20*" --query "reverse(sort_by(Images, &CreationDate))[0].ImageId" --region $Region --output text
Write-Host "   AMI: $amiId" -ForegroundColor Green

# Step 4: Launch Instance  
Write-Host ""
Write-Host "[4/4] Launching GPU Instance..." -ForegroundColor Yellow
Write-Host "   Instance Type: $InstanceType (NVIDIA T4 GPU)" -ForegroundColor White

# Create block device mapping file
$bdmFile = "$env:TEMP\bdm.json"
'[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' | Out-File -FilePath $bdmFile -Encoding ASCII

$instanceId = aws ec2 run-instances `
    --image-id $amiId `
    --instance-type $InstanceType `
    --key-name $KeyPairName `
    --security-group-ids $sgId `
    --block-device-mappings file://$bdmFile `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=AI-Video-Clipper}]" `
    --region $Region `
    --query "Instances[0].InstanceId" `
    --output text

Remove-Item $bdmFile -Force -ErrorAction SilentlyContinue

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($instanceId)) {
    Write-Host "   FAILED to launch instance!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Possible reasons:" -ForegroundColor Yellow
    Write-Host "   1. GPU instance quota = 0 (need to request increase)" -ForegroundColor White
    Write-Host "   2. Region doesn't support g4dn instances" -ForegroundColor White
    Write-Host ""
    Write-Host "   Request quota increase at:" -ForegroundColor Yellow
    Write-Host "   https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Search for: 'Running On-Demand G and VT instances'" -ForegroundColor White
    exit 1
}

Write-Host "   Instance ID: $instanceId" -ForegroundColor Green

# Wait for running
Write-Host ""
Write-Host "Waiting for instance to start..." -ForegroundColor Yellow
aws ec2 wait instance-running --instance-ids $instanceId --region $Region

# Get Public IP
$publicIp = aws ec2 describe-instances --instance-ids $instanceId --region $Region --query "Reservations[0].Instances[0].PublicIpAddress" --output text

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   INSTANCE LAUNCHED!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Instance Details:" -ForegroundColor Cyan
Write-Host "   ID:   $instanceId"
Write-Host "   IP:   $publicIp"
Write-Host "   Type: $InstanceType"
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. SSH ke server (tunggu 1 menit):" -ForegroundColor White
Write-Host "   ssh -i $keyPath\$KeyPairName.pem ubuntu@$publicIp"
Write-Host ""
Write-Host "2. Di server, jalankan setup:" -ForegroundColor White
Write-Host "   curl -fsSL https://raw.githubusercontent.com/astika327-dev/clipping/main/aws_setup.sh | bash"
Write-Host ""
Write-Host "3. Setelah selesai (~10 menit), akses:" -ForegroundColor White
Write-Host "   http://$publicIp" -ForegroundColor Cyan
Write-Host ""
Write-Host "BIAYA: ~`$0.526/jam" -ForegroundColor Red
Write-Host "Stop dengan: aws ec2 stop-instances --instance-ids $instanceId --region $Region" -ForegroundColor Gray
Write-Host ""

# Save instance ID
$instanceId | Out-File -FilePath "$PSScriptRoot\instance-id.txt" -Encoding ASCII
Write-Host "Instance ID saved to: $PSScriptRoot\instance-id.txt" -ForegroundColor Green
