# ================================================
# AI Video Clipper - Initial AWS Setup
# ================================================
# Run this ONCE after creating your EC2 instance
# ================================================

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Video Clipper - AWS Configuration" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI tidak ditemukan!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install dengan salah satu cara:" -ForegroundColor Yellow
    Write-Host "  1. winget install Amazon.AWSCLI" -ForegroundColor White
    Write-Host "  2. Download dari https://aws.amazon.com/cli/" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ AWS CLI ditemukan" -ForegroundColor Green
Write-Host ""

# Check if already configured
$IDENTITY = aws sts get-caller-identity 2>$null | ConvertFrom-Json

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ AWS sudah dikonfigurasi" -ForegroundColor Green
    Write-Host "   Account: $($IDENTITY.Account)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  AWS credentials belum dikonfigurasi." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Jalankan 'aws configure' dan masukkan:" -ForegroundColor Cyan
    Write-Host "  - Access Key ID" -ForegroundColor White
    Write-Host "  - Secret Access Key" -ForegroundColor White
    Write-Host "  - Region (contoh: ap-southeast-1)" -ForegroundColor White
    Write-Host ""
    
    $configure = Read-Host "Configure sekarang? (y/N)"
    if ($configure -eq "y" -or $configure -eq "Y") {
        aws configure
    } else {
        exit 1
    }
}

# List EC2 instances
Write-Host "📋 Mencari EC2 instances..." -ForegroundColor Yellow
Write-Host ""

$INSTANCES = aws ec2 describe-instances `
    --query "Reservations[].Instances[].{ID:InstanceId,Name:Tags[?Key=='Name'].Value|[0],Type:InstanceType,State:State.Name,IP:PublicIpAddress}" `
    --output json 2>$null | ConvertFrom-Json

if ($INSTANCES.Count -eq 0) {
    Write-Host "❌ Tidak ada EC2 instances ditemukan." -ForegroundColor Red
    Write-Host ""
    Write-Host "Buat instance baru:" -ForegroundColor Yellow
    Write-Host "  1. Buka AWS Console: https://console.aws.amazon.com/ec2" -ForegroundColor White
    Write-Host "  2. Launch Instance dengan template g4dn.xlarge" -ForegroundColor White
    Write-Host "  3. Atau gunakan CloudFormation template" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "🖥️  EC2 Instances yang ditemukan:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   ID                    Name                    Type           State" -ForegroundColor White
Write-Host "   ─────────────────────────────────────────────────────────────────────" -ForegroundColor Gray

$index = 1
foreach ($inst in $INSTANCES) {
    $stateColor = if ($inst.State -eq "running") { "Green" } elseif ($inst.State -eq "stopped") { "Red" } else { "Yellow" }
    Write-Host ("   [{0}] {1}  {2,-20}  {3,-12}  " -f $index, $inst.ID, $inst.Name, $inst.Type) -NoNewline
    Write-Host $inst.State -ForegroundColor $stateColor
    $index++
}

Write-Host ""
$selection = Read-Host "Pilih nomor instance untuk AI Video Clipper (1-$($INSTANCES.Count))"

if ($selection -lt 1 -or $selection -gt $INSTANCES.Count) {
    Write-Host "❌ Pilihan tidak valid." -ForegroundColor Red
    exit 1
}

$SELECTED = $INSTANCES[$selection - 1]
$INSTANCE_ID = $SELECTED.ID

Write-Host ""
Write-Host "✅ Instance terpilih: $INSTANCE_ID ($($SELECTED.Name))" -ForegroundColor Green
Write-Host ""

# Get region
$REGION = aws configure get region

# Update scripts
Write-Host "📝 Updating scripts..." -ForegroundColor Yellow

$scriptsPath = $PSScriptRoot

# Update start-clipper.ps1
$startScript = Get-Content "$scriptsPath\start-clipper.ps1" -Raw
$startScript = $startScript -replace 'i-XXXXXXXXXXXXX', $INSTANCE_ID
$startScript = $startScript -replace 'ap-southeast-1', $REGION
Set-Content "$scriptsPath\start-clipper.ps1" $startScript

# Update stop-clipper.ps1
$stopScript = Get-Content "$scriptsPath\stop-clipper.ps1" -Raw
$stopScript = $stopScript -replace 'i-XXXXXXXXXXXXX', $INSTANCE_ID
$stopScript = $stopScript -replace 'ap-southeast-1', $REGION
Set-Content "$scriptsPath\stop-clipper.ps1" $stopScript

# Update status-clipper.ps1
$statusScript = Get-Content "$scriptsPath\status-clipper.ps1" -Raw
$statusScript = $statusScript -replace 'i-XXXXXXXXXXXXX', $INSTANCE_ID
$statusScript = $statusScript -replace 'ap-southeast-1', $REGION
Set-Content "$scriptsPath\status-clipper.ps1" $statusScript

# Update download-clips.ps1
$downloadScript = Get-Content "$scriptsPath\download-clips.ps1" -Raw
$downloadScript = $downloadScript -replace 'i-XXXXXXXXXXXXX', $INSTANCE_ID
$downloadScript = $downloadScript -replace 'ap-southeast-1', $REGION
Set-Content "$scriptsPath\download-clips.ps1" $downloadScript

Write-Host "✅ Scripts updated!" -ForegroundColor Green
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Instance ID : $INSTANCE_ID" -ForegroundColor Cyan
Write-Host "Region      : $REGION" -ForegroundColor Cyan
Write-Host ""
Write-Host "Gunakan scripts ini:" -ForegroundColor Yellow
Write-Host "  .\start-clipper.ps1   - Start instance" -ForegroundColor White
Write-Host "  .\stop-clipper.ps1    - Stop instance (HEMAT!)" -ForegroundColor White
Write-Host "  .\status-clipper.ps1  - Check status" -ForegroundColor White
Write-Host "  .\download-clips.ps1  - Download hasil clips" -ForegroundColor White
Write-Host ""

# Ask to start now
$startNow = Read-Host "Start instance sekarang? (y/N)"
if ($startNow -eq "y" -or $startNow -eq "Y") {
    & "$scriptsPath\start-clipper.ps1"
}
