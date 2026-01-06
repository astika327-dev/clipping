# 🐳 Docker AWS Deployment Guide

Panduan lengkap untuk deploy AI Video Clipper ke AWS menggunakan Docker.

## 📋 Prerequisites

1. **AWS CLI** terinstall dan terkonfigurasi
2. **GitHub Personal Access Token (classic)** dengan permission:
   - `write:packages`
   - `read:packages`
   - (optional) `delete:packages`
3. **AWS Account** dengan akses ke GPU instances (g4dn)

## 🚀 Quick Start

### Step 1: Build & Push Docker Image ke GHCR

Ada 2 cara untuk push image:

#### Opsi A: Manual Build & Push (Lokal)

```bash
# Login ke GitHub Container Registry
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Build image
docker build -t ghcr.io/astika327-dev/clipping:latest .

# Push ke GHCR
docker push ghcr.io/astika327-dev/clipping:latest
```

#### Opsi B: Otomatis via GitHub Actions (Recommended)

Cukup push ke branch `main`, dan GitHub Actions akan otomatis build & push!

```bash
git push origin main
```

Cek progress di: `https://github.com/astika327-dev/clipping/actions`

### Step 2: Deploy ke AWS

```powershell
# Deploy dengan token (otomatis pull image)
.\aws-scripts\deploy-docker.ps1 -GitHubToken "ghp_xxxx"

# Atau deploy tanpa token (manual pull nanti)
.\aws-scripts\deploy-docker.ps1
```

### Step 3: Akses Aplikasi

Setelah ~5-7 menit, akses di: `http://YOUR_EC2_IP`

## 📖 Commands Reference

### Deploy Commands

```powershell
# Deploy instance baru
.\aws-scripts\deploy-docker.ps1 -Action deploy

# Dengan spesifik instance type
.\aws-scripts\deploy-docker.ps1 -Action deploy -InstanceType "g4dn.2xlarge"

# Dengan region berbeda
.\aws-scripts\deploy-docker.ps1 -Action deploy -Region "us-west-2"
```

### Management Commands

```powershell
# Cek status instance
.\aws-scripts\deploy-docker.ps1 -Action status

# Info untuk update
.\aws-scripts\deploy-docker.ps1 -Action update

# Delete instance
.\aws-scripts\deploy-docker.ps1 -Action delete
```

### SSH ke Instance

```bash
ssh -i ~/.ssh/clipper-key.pem ubuntu@YOUR_EC2_IP
```

### Di dalam Instance

```bash
# Cek status containers
docker ps

# Lihat logs
docker logs -f ai-video-clipper

# Update ke image terbaru
cd /home/ubuntu/clipper
./update.sh

# Restart containers
docker compose restart

# Stop containers
docker compose down

# Start containers
docker compose up -d
```

## ⚙️ Konfigurasi

### Environment Variables

Edit file `/home/ubuntu/clipper/.env` di instance:

```bash
nano /home/ubuntu/clipper/.env
```

Important variables:

- `GROQ_API_KEY` - API key untuk LLM
- `FASTER_WHISPER_MODEL` - Model size (tiny/base/small/medium/large-v3)
- `MAX_CLIPS_PER_VIDEO` - Maksimal clips per video

Setelah edit, restart container:

```bash
docker compose restart
```

### Volumes

Data disimpan di:

- `/home/ubuntu/clipper/data/uploads` - Video uploads
- `/home/ubuntu/clipper/data/outputs` - Generated clips

## 💰 Cost Optimization

### Stop Instance Saat Tidak Digunakan

```powershell
# Stop
aws ec2 stop-instances --instance-ids i-xxxxx --region ap-southeast-1

# Start
aws ec2 start-instances --instance-ids i-xxxxx --region ap-southeast-1
```

### Instance Types & Pricing (ap-southeast-1)

| Type         | GPU   | vCPU | RAM  | On-Demand/hr |
| ------------ | ----- | ---- | ---- | ------------ |
| g4dn.xlarge  | 1x T4 | 4    | 16GB | ~$0.71       |
| g4dn.2xlarge | 1x T4 | 8    | 32GB | ~$1.06       |
| g4dn.4xlarge | 1x T4 | 16   | 64GB | ~$1.70       |

## 🔄 Update Workflow

### Auto-Update (GitHub Actions)

1. Push code ke `main` branch
2. GitHub Actions build image baru
3. SSH ke instance dan run:
   ```bash
   cd /home/ubuntu/clipper && ./update.sh
   ```

### Manual Update

```bash
# Di instance
cd /home/ubuntu/clipper

# Login jika perlu
echo "YOUR_TOKEN" | docker login ghcr.io -u astika327-dev --password-stdin

# Pull & restart
docker compose pull
docker compose up -d
```

## 🔧 Troubleshooting

### GPU Tidak Terdeteksi

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

### Container Tidak Start

```bash
# Check logs
docker logs ai-video-clipper

# Check docker-compose
docker compose logs
```

### Pull Image Gagal

```bash
# Re-login ke GHCR
echo "YOUR_TOKEN" | docker login ghcr.io -u astika327-dev --password-stdin

# Retry pull
docker compose pull
```

## 📊 Monitoring

### Container Stats

```bash
docker stats
```

### Disk Usage

```bash
df -h
docker system df
```

### Clean Up

```bash
# Remove unused images
docker system prune -f

# Remove all unused data (careful!)
docker system prune -a
```

## 🔐 Security Tips

1. **Jangan commit GitHub Token** - Gunakan environment variable atau secrets
2. **Limit Security Group** - Hanya buka port yang diperlukan
3. **Update regular** - Pull image terbaru untuk security patches
4. **Use IAM roles** - Untuk akses AWS services dari container
