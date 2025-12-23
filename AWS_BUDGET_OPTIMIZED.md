# 💰 AWS Budget Optimized Configuration ($119 Credit)

Panduan konfigurasi AWS yang dioptimalkan untuk kredit $119.

---

## 📊 Budget Analysis

| Item             | Biaya Estimasi | Catatan                  |
| ---------------- | -------------- | ------------------------ |
| **Total Credit** | **$119**       | AWS Free Tier kredit     |
| Target Usage     | 60-90 hari     | Tergantung usage pattern |

---

## 🎯 Recommended Instance Configuration

### **PILIHAN UTAMA: g4dn.xlarge (On-Demand)**

| Spec              | Value                 |
| ----------------- | --------------------- |
| **Instance Type** | g4dn.xlarge           |
| **vCPU**          | 4                     |
| **RAM**           | 16 GB                 |
| **GPU**           | NVIDIA T4 (16GB VRAM) |
| **Cost/hour**     | ~$0.526               |
| **Storage**       | 50GB gp3 (~$4/month)  |

### 💡 Estimasi Penggunaan dengan $119

| Skenario         | Jam/Hari | Hari Aktif    | Total Jam | Est. Cost | Durasi Budget  |
| ---------------- | -------- | ------------- | --------- | --------- | -------------- |
| **Hemat**        | 1 jam    | 5 hari/minggu | ~86 jam   | ~$49      | **~10 minggu** |
| **Standar**      | 2 jam    | 5 hari/minggu | ~172 jam  | ~$95      | **~5 minggu**  |
| **Intensif**     | 4 jam    | 5 hari/minggu | ~344 jam  | ~$185     | **~3 minggu**  |
| **Weekend Only** | 3 jam    | 2 hari/minggu | ~52 jam   | ~$31      | **~16 minggu** |

---

## 🔧 Optimized Software Configuration

### Backend `.env` (Production Optimized)

```env
# ============================================
# AWS BUDGET OPTIMIZED CONFIGURATION
# ============================================

# === TRANSCRIPTION (Optimized for T4 GPU) ===
TRANSCRIPTION_BACKEND=faster-whisper
FASTER_WHISPER_MODEL=medium          # medium lebih hemat dari large-v3
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16  # float16 untuk efisiensi
FASTER_WHISPER_BEAM_SIZE=3           # Kurangi dari 5 untuk speed

# === HYBRID TRANSCRIPTION ===
HYBRID_TRANSCRIPTION_ENABLED=true
CONFIDENCE_RETRY_THRESHOLD=0.65      # Sedikit lebih rendah untuk mengurangi retry
GROQ_API_ENABLED=true
GROQ_API_KEY=your_groq_key_here      # Backup transcription (gratis)

# === LLM INTELLIGENCE ===
LLM_PROVIDER=groq                    # Gunakan Groq (gratis)
LLM_MODEL=llama-3.3-70b-versatile    # Model gratis yang powerful

# === DEEP LEARNING VIDEO ===
ENABLE_DEEP_LEARNING_VIDEO=true
YOLO_MODEL_SIZE=n                    # nano = tercepat, hemat VRAM
ENABLE_FACE_DETECTION=true
MEDIAPIPE_MODEL_COMPLEXITY=0         # 0 = fastest

# === PERFORMANCE (Optimized for 16GB T4) ===
MAX_CLIPS_PER_VIDEO=20               # Batasi clips per video
PROCESSING_CONCURRENCY=1             # Single process untuk stabilitas
MAX_VIDEO_DURATION=3600              # Max 1 jam video
MAX_UPLOAD_SIZE=2147483648           # 2GB max upload

# === GPU MEMORY MANAGEMENT ===
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256
CUDA_VISIBLE_DEVICES=0

# === AUTO-CLEANUP ===
AUTO_CLEANUP_ENABLED=true
CLEANUP_AGE_HOURS=24                 # Hapus hasil setelah 24 jam
```

---

## 📦 CloudFormation Parameters (Budget Optimized)

```yaml
Parameters:
  InstanceType: g4dn.xlarge # Best value GPU
  VolumeSize: 50 # 50GB cukup untuk most use cases
  AllowedSSHIP: YOUR_IP/32 # Restrict SSH untuk keamanan
```

### 💾 Storage Optimization

| Volume Size | Cost/Month | Use Case               |
| ----------- | ---------- | ---------------------- |
| **50GB**    | **~$4**    | ✅ Recommended (hemat) |
| 75GB        | ~$6        | Medium processing      |
| 100GB       | ~$8        | Heavy processing       |

---

## 🚀 Quick Launch Commands

### Option 1: AWS CLI (Recommended)

```powershell
# Launch Budget-Optimized Instance
aws ec2 run-instances `
    --image-id ami-078c1149d8ad719a7 `
    --instance-type g4dn.xlarge `
    --key-name your-key-pair `
    --security-group-ids sg-xxxxxxxx `
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' `
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=AI-Video-Clipper}]' `
    --count 1
```

### Option 2: CloudFormation (One-Click)

```powershell
aws cloudformation create-stack `
    --stack-name ai-video-clipper `
    --template-body file://aws-cloudformation-budget.yaml `
    --parameters `
        ParameterKey=InstanceType,ParameterValue=g4dn.xlarge `
        ParameterKey=VolumeSize,ParameterValue=50 `
        ParameterKey=KeyName,ParameterValue=your-key-pair `
    --capabilities CAPABILITY_NAMED_IAM
```

---

## ⚡ Maximum Savings Strategy

### 1. **On-Demand Pattern (WAJIB!)**

```
┌─────────────────────────────────────────────────────────┐
│              DAILY WORKFLOW - MAKSIMUM HEMAT            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ⏰ SEBELUM KERJA                                        │
│  └── .\aws-scripts\start-clipper.ps1                    │
│                                                          │
│  📤 BATCH UPLOAD                                         │
│  └── Upload SEMUA video sekaligus                       │
│  └── Jangan start-stop untuk single video!              │
│                                                          │
│  ⚙️ PROCESS                                              │
│  └── Process semua video dalam 1 session                │
│                                                          │
│  📥 DOWNLOAD                                             │
│  └── Download SEMUA hasil clips                         │
│                                                          │
│  🛑 STOP INSTANCE (CRITICAL!)                           │
│  └── .\aws-scripts\stop-clipper.ps1                     │
│  └── SETIAP MENIT = $0.0088 💸                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2. **Gunakan Spot Instance untuk Batch Processing**

```powershell
# Spot Instance = 70-90% LEBIH MURAH!
# g4dn.xlarge Spot = ~$0.16/jam vs $0.526/jam

aws ec2 request-spot-instances `
    --instance-count 1 `
    --type "one-time" `
    --launch-specification file://spot-spec.json
```

**⚠️ Catatan Spot**: Bisa di-interrupt, cocok untuk batch non-critical.

### 3. **Auto-Stop Safety Net**

```bash
# Tambahkan auto-stop di EC2 (crontab)
# Auto shutdown setelah 2 jam idle

0 */2 * * * /home/ubuntu/check_and_stop.sh
```

---

## 📊 Budget Tracker

### Template untuk Track Penggunaan

```
┌────────────────────────────────────────────────────────┐
│                    BUDGET TRACKER                       │
├────────────────────────────────────────────────────────┤
│ Starting Credit:     $119.00                            │
│ Current Balance:     $___.__                            │
│ Days Used:           __ hari                            │
│ Total Hours:         __ jam                             │
│ Avg Cost/Day:        $_.__                              │
│ Est. Days Remaining: __ hari                            │
└────────────────────────────────────────────────────────┘
```

### AWS Cost Explorer

```powershell
# Check daily cost
aws ce get-cost-and-usage `
    --time-period Start=2024-12-01,End=2024-12-31 `
    --granularity DAILY `
    --metrics BlendedCost
```

---

## 🎮 Model Size Comparison (Choose Based on Needs)

### Whisper Models

| Model      | VRAM Usage | Speed      | Accuracy | Recommendation     |
| ---------- | ---------- | ---------- | -------- | ------------------ |
| tiny       | ~1GB       | ⚡⚡⚡⚡⚡ | 60%      | Testing only       |
| base       | ~1.5GB     | ⚡⚡⚡⚡   | 74%      | Quick drafts       |
| small      | ~2GB       | ⚡⚡⚡     | 80%      | Good balance       |
| **medium** | **~5GB**   | **⚡⚡**   | **85%**  | ✅ **Recommended** |
| large-v3   | ~10GB      | ⚡         | 90%      | Premium quality    |

### YOLO Models

| Model        | Size      | Speed          | Accuracy | VRAM        |
| ------------ | --------- | -------------- | -------- | ----------- |
| **nano (n)** | **3.2MB** | **⚡⚡⚡⚡⚡** | 37%      | **~1GB** ✅ |
| small (s)    | 11.2MB    | ⚡⚡⚡⚡       | 44%      | ~2GB        |
| medium (m)   | 25.9MB    | ⚡⚡⚡         | 50%      | ~4GB        |

---

## 🛡️ Cost Protection Settings

### 1. AWS Budget Alert

```powershell
# Create budget alert at $100
aws budgets create-budget `
    --account-id YOUR_ACCOUNT_ID `
    --budget file://budget.json `
    --notifications-with-subscribers file://notifications.json
```

### 2. CloudWatch Billing Alarm

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name "BillingAlarm-100USD" \
    --alarm-description "Alarm when estimated charges reach $100" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Maximum \
    --period 21600 \
    --threshold 100 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=Currency,Value=USD \
    --evaluation-periods 1 \
    --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:billing-alerts
```

---

## 📋 Pre-Launch Checklist

- [ ] AWS CLI installed & configured
- [ ] EC2 Key Pair created
- [ ] Security Group configured (ports 22, 80, 443, 5000)
- [ ] VPC & Subnet selected (use default jika baru)
- [ ] Budget Alert set at $100
- [ ] Download start/stop scripts ke PC lokal
- [ ] Groq API Key ready (gratis dari console.groq.com)

---

## 🚨 PENTING: Cost Saving Reminders

1. **SELALU STOP INSTANCE** setelah selesai processing
2. **Gunakan Spot Instance** untuk batch processing besar
3. **Batch Processing** - kumpulkan video, process sekaligus
4. **Monitor di AWS Console** - check billing daily
5. **Set Budget Alerts** - notifikasi sebelum habis
6. **Gunakan medium Whisper** - balance antara speed & quality
7. **Auto-cleanup outputs** - hemat storage

---

## 💡 Pro Tips untuk $119 Credit

| Tip                             | Savings              |
| ------------------------------- | -------------------- |
| Stop instance saat idle         | Up to 90%            |
| Gunakan Spot untuk batch        | 70-90% per session   |
| Gunakan Whisper medium vs large | 2x faster, less VRAM |
| Gunakan YOLO nano vs small      | 3x faster            |
| 50GB storage vs 100GB           | $4/month saved       |
| Auto-cleanup setelah 24jam      | Storage hemat        |

---

**Target Realistis dengan $119:**

- **Conservative (Weekend warrior)**: ~4 bulan usage
- **Standard (Casual user)**: ~6-8 minggu
- **Intensive (Daily creator)**: ~3-4 minggu

---

**Last Updated**: December 2024
**Optimized For**: AWS $119 Free Credit + g4dn.xlarge
