# 🎮 AWS Control Scripts

PowerShell scripts untuk mengelola AI Video Clipper di AWS.

## 🚀 Quick Start

### 1. Setup Pertama Kali

```powershell
cd aws-scripts
.\setup-aws.ps1
```

Script ini akan:

- Check AWS CLI installation
- Configure AWS credentials (jika belum)
- List semua EC2 instances
- Update semua scripts dengan Instance ID yang benar

### 2. Penggunaan Harian

```powershell
# START - Mulai instance (1-2 menit)
.\start-clipper.ps1

# Gunakan aplikasi di browser...

# STOP - Matikan instance (PENTING untuk hemat biaya!)
.\stop-clipper.ps1
```

## 📁 Scripts

| Script               | Fungsi                            |
| -------------------- | --------------------------------- |
| `setup-aws.ps1`      | Setup awal, configure Instance ID |
| `start-clipper.ps1`  | Start EC2 instance                |
| `stop-clipper.ps1`   | Stop EC2 instance (hemat!)        |
| `status-clipper.ps1` | Check status instance             |
| `download-clips.ps1` | Download clips ke PC lokal        |

## 💰 Biaya

| Action           | Biaya      |
| ---------------- | ---------- |
| Instance RUNNING | $0.526/jam |
| Instance STOPPED | $0/jam     |
| Storage (EBS)    | ~$8/bulan  |

**SELALU stop instance setelah selesai!**

## 🔧 Requirements

1. **AWS CLI** - Install dengan:

   ```powershell
   winget install Amazon.AWSCLI
   ```

2. **AWS Credentials** - Dapatkan dari IAM Console:
   - Access Key ID
   - Secret Access Key

## ❓ Troubleshooting

### "AWS CLI tidak ditemukan"

```powershell
winget install Amazon.AWSCLI
# Restart PowerShell
```

### "Instance ID belum dikonfigurasi"

```powershell
.\setup-aws.ps1
```

### "Failed to get instance status"

```powershell
aws configure
# Re-enter credentials
```
