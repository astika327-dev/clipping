# 💰 AWS On-Demand Guide (Pay When You Use)

Panduan untuk menggunakan AWS **hanya saat diperlukan** - hemat hingga 90% biaya!

---

## 📊 Perbandingan Biaya

| Mode                       | Biaya/Bulan | Catatan             |
| -------------------------- | ----------- | ------------------- |
| 24/7 Running               | ~$400       | ❌ Mahal            |
| **On-Demand (4 jam/hari)** | **~$65**    | ✅ Hemat 84%        |
| **On-Demand (1 jam/hari)** | **~$16**    | ✅ Hemat 96%        |
| Spot Instance              | ~$50-80     | ⚠️ Bisa interrupted |

---

## 🎯 Cara Kerja On-Demand

```
1. Perlu process video → Start Instance (1-2 menit boot)
2. Upload & Process video → Selesai dalam X menit
3. Download hasil → Stop Instance
4. 💰 Bayar hanya waktu yang dipakai!
```

---

## 🖥️ METHOD 1: Manual via AWS Console

### Start Instance:

1. Buka [AWS EC2 Console](https://console.aws.amazon.com/ec2)
2. Pilih instance "AI-Video-Clipper"
3. **Actions → Instance State → Start**
4. Tunggu status "Running" (~1-2 menit)
5. Akses via Public IP baru

### Stop Instance:

1. Setelah selesai, **Actions → Instance State → Stop**
2. ✅ Tidak ada biaya compute (hanya biaya storage ~$8/bulan)

---

## 🔧 METHOD 2: AWS CLI (Recommended)

### Setup AWS CLI di PC Lokal:

```powershell
# Install AWS CLI (Windows)
winget install Amazon.AWSCLI

# Configure
aws configure
# Masukkan: Access Key, Secret Key, Region (ap-southeast-1)
```

### Start Instance:

```powershell
# Start instance
aws ec2 start-instances --instance-ids i-YOUR_INSTANCE_ID

# Tunggu sampai running
aws ec2 wait instance-running --instance-ids i-YOUR_INSTANCE_ID

# Get Public IP baru
aws ec2 describe-instances --instance-ids i-YOUR_INSTANCE_ID --query "Reservations[0].Instances[0].PublicIpAddress" --output text
```

### Stop Instance:

```powershell
# Stop instance (PENTING setelah selesai!)
aws ec2 stop-instances --instance-ids i-YOUR_INSTANCE_ID
```

---

## ⚡ METHOD 3: PowerShell Scripts (Easiest)

Simpan scripts ini untuk kemudahan:

### `start-clipper.ps1`:

```powershell
# Start AI Video Clipper on AWS
$INSTANCE_ID = "i-YOUR_INSTANCE_ID"  # Ganti dengan Instance ID kamu

Write-Host "🚀 Starting AI Video Clipper..." -ForegroundColor Cyan

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID | Out-Null

Write-Host "⏳ Waiting for instance to start..." -ForegroundColor Yellow
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
$PUBLIC_IP = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --query "Reservations[0].Instances[0].PublicIpAddress" `
    --output text

Write-Host ""
Write-Host "✅ Instance is running!" -ForegroundColor Green
Write-Host "🌐 Access your app at: http://$PUBLIC_IP" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  JANGAN LUPA: Jalankan stop-clipper.ps1 setelah selesai!" -ForegroundColor Yellow

# Open browser
Start-Process "http://$PUBLIC_IP"
```

### `stop-clipper.ps1`:

```powershell
# Stop AI Video Clipper on AWS
$INSTANCE_ID = "i-YOUR_INSTANCE_ID"  # Ganti dengan Instance ID kamu

Write-Host "🛑 Stopping AI Video Clipper..." -ForegroundColor Cyan

# Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID | Out-Null

Write-Host "⏳ Waiting for instance to stop..." -ForegroundColor Yellow
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

Write-Host ""
Write-Host "✅ Instance stopped! No more compute charges." -ForegroundColor Green
Write-Host "💰 Storage cost only: ~$8/month for 100GB EBS" -ForegroundColor Cyan
```

### `status-clipper.ps1`:

```powershell
# Check status of AI Video Clipper
$INSTANCE_ID = "i-YOUR_INSTANCE_ID"

$STATUS = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --query "Reservations[0].Instances[0].State.Name" `
    --output text

$IP = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --query "Reservations[0].Instances[0].PublicIpAddress" `
    --output text

Write-Host "📊 Instance Status: $STATUS" -ForegroundColor Cyan
if ($STATUS -eq "running") {
    Write-Host "🌐 URL: http://$IP" -ForegroundColor Green
}
```

---

## 📱 METHOD 4: Mobile App (AWS Console App)

1. Download **AWS Console** app di smartphone
2. Login dengan AWS account
3. Bisa Start/Stop instance dari HP kapan saja!

---

## ⏰ METHOD 5: Auto Stop (Schedule)

Hindari lupa stop dengan auto-shutdown:

### Option A: Instance Scheduler (AWS)

```bash
# Install di EC2 (auto shutdown setelah 2 jam idle)
sudo crontab -e
# Tambahkan:
0 * * * * /home/ubuntu/check_idle.sh
```

### `check_idle.sh`:

```bash
#!/bin/bash
# Auto shutdown jika idle 30 menit

IDLE_THRESHOLD=1800  # 30 menit dalam detik

# Check CPU usage
CPU_IDLE=$(top -bn1 | grep "Cpu(s)" | awk '{print $8}')

# Check if no active processing
if [ $(echo "$CPU_IDLE > 95" | bc) -eq 1 ]; then
    IDLE_TIME=$((IDLE_TIME + 3600))
    if [ $IDLE_TIME -ge $IDLE_THRESHOLD ]; then
        sudo shutdown -h now
    fi
else
    IDLE_TIME=0
fi
```

### Option B: EventBridge Schedule

```bash
# Auto stop setiap jam 23:00 WIB
aws events put-rule \
    --name "StopClipperNightly" \
    --schedule-expression "cron(0 16 * * ? *)"
```

---

## 🔄 Workflow Harian

```
┌─────────────────────────────────────────────────────────┐
│                   DAILY WORKFLOW                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. 🚀 Start Instance                                   │
│     └── .\start-clipper.ps1                             │
│     └── Tunggu 1-2 menit                                │
│                                                          │
│  2. 📤 Upload Video                                     │
│     └── Buka http://PUBLIC_IP                           │
│     └── Upload video atau paste YouTube URL            │
│                                                          │
│  3. ⚙️ Process                                          │
│     └── Pilih settings                                  │
│     └── Tunggu processing (5-30 menit)                  │
│                                                          │
│  4. 📥 Download Clips                                   │
│     └── Download semua clips                            │
│                                                          │
│  5. 🛑 STOP INSTANCE (PENTING!)                        │
│     └── .\stop-clipper.ps1                              │
│     └── Hemat $0.50+ per jam!                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Tips Hemat Maksimal

### 1. Batch Processing

```
❌ Process 1 video, stop, start, process 1 video lagi
✅ Kumpulkan video, start 1x, process semua, stop 1x
```

### 2. Gunakan Elastic IP (Optional)

```bash
# Allocate Elastic IP (gratis jika attached ke running instance)
aws ec2 allocate-address --domain vpc

# Associate ke instance
aws ec2 associate-address --instance-id i-xxx --allocation-id eipalloc-xxx

# Benefit: IP tetap sama setiap start
```

⚠️ Warning: Elastic IP yang TIDAK attached = $3.65/bulan

### 3. Smaller EBS Volume

```
100GB = $8/bulan
50GB = $4/bulan (jika tidak perlu banyak storage)
```

### 4. Spot Instance (Untuk Advanced User)

```bash
# 70-90% lebih murah, tapi bisa di-interrupt
aws ec2 request-spot-instances \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification file://spot-spec.json
```

---

## 📊 Kalkulasi Biaya On-Demand

| Penggunaan   | Jam/Bulan | Biaya Compute | Storage | Total    |
| ------------ | --------- | ------------- | ------- | -------- |
| 1 jam/hari   | 30 jam    | $15.78        | $8      | **~$24** |
| 2 jam/hari   | 60 jam    | $31.56        | $8      | **~$40** |
| 4 jam/hari   | 120 jam   | $63.12        | $8      | **~$71** |
| Weekend only | 16 jam    | $8.42         | $8      | **~$17** |

\*Berdasarkan g4dn.xlarge @ $0.526/jam

---

## ⚠️ REMINDER

**SELALU STOP INSTANCE SETELAH SELESAI!**

Buat reminder di HP atau gunakan auto-stop schedule.

---

**Last Updated**: December 2024
