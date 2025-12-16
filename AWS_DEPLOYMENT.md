# 🚀 AWS Cloud Deployment Guide

Panduan lengkap untuk deploy AI Video Clipper ke AWS Cloud dengan optimasi maksimal.

---

## 📊 ARSITEKTUR OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐     ┌──────────────────────────────────────────┐     │
│   │   Route 53  │────►│           CloudFront CDN                 │     │
│   │   (Domain)  │     │    (Frontend Static Files Cache)         │     │
│   └─────────────┘     └──────────────────┬───────────────────────┘     │
│                                          │                              │
│                                          ▼                              │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │              Application Load Balancer (ALB)                  │     │
│   │                    (HTTPS Termination)                        │     │
│   └───────────────────────────┬──────────────────────────────────┘     │
│                               │                                         │
│              ┌────────────────┼────────────────┐                       │
│              ▼                ▼                ▼                       │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│   │   EC2 GPU    │  │   EC2 GPU    │  │   EC2 GPU    │                │
│   │  Instance 1  │  │  Instance 2  │  │  Instance N  │                │
│   │  (g4dn/p3)   │  │  (g4dn/p3)   │  │  (g4dn/p3)   │                │
│   └───────┬──────┘  └───────┬──────┘  └───────┬──────┘                │
│           │                 │                 │                         │
│           └─────────────────┼─────────────────┘                         │
│                             ▼                                           │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │                        S3 Bucket                              │     │
│   │     (Video Uploads, Generated Clips, Static Assets)          │     │
│   └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │                    Redis ElastiCache                          │     │
│   │              (Job Queue & Session Storage)                    │     │
│   └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 DEPLOYMENT OPTIONS

### Option 1: **EC2 GPU Instance** (Recommended untuk Production)

- **Best for**: Production, high-volume processing
- **Cost**: $0.526/hr (g4dn.xlarge) - $3.06/hr (p3.2xlarge)
- **GPU**: NVIDIA T4 (g4dn) atau V100 (p3)

### Option 2: **ECS/EKS with GPU**

- **Best for**: Auto-scaling, container orchestration
- **Cost**: Base EC2 + container overhead
- **Complexity**: Higher, but more scalable

### Option 3: **AWS Lambda + SageMaker**

- **Best for**: Serverless, pay-per-use
- **Cost**: Per invocation
- **Limitation**: Cold start, timeout limits

**Rekomendasi**: Untuk AI Video Clipper, gunakan **Option 1 (EC2 GPU)** karena processing video membutuhkan GPU persistent dan file access yang cepat.

---

## 🖥️ PILIHAN INSTANCE TYPE

| Instance Type   | vCPU | RAM  | GPU     | GPU Memory | Cost/hr | Recommendation |
| --------------- | ---- | ---- | ------- | ---------- | ------- | -------------- |
| **g4dn.xlarge** | 4    | 16GB | 1x T4   | 16GB       | ~$0.526 | ✅ Best Value  |
| g4dn.2xlarge    | 8    | 32GB | 1x T4   | 16GB       | ~$0.752 | Good Balance   |
| g4dn.4xlarge    | 16   | 64GB | 1x T4   | 16GB       | ~$1.204 | High CPU Tasks |
| g5.xlarge       | 4    | 16GB | 1x A10G | 24GB       | ~$1.006 | Newer GPU      |
| **p3.2xlarge**  | 8    | 61GB | 1x V100 | 16GB       | ~$3.06  | 🚀 Fastest     |

**Rekomendasi**: **g4dn.xlarge** untuk starting, upgrade ke **g4dn.2xlarge** atau **p3.2xlarge** untuk volume tinggi.

---

## 🔧 STEP-BY-STEP DEPLOYMENT

### Step 1: Launch EC2 GPU Instance

```bash
# AWS CLI command untuk launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type g4dn.xlarge \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxx \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=AI-Video-Clipper}]' \
  --count 1
```

**Atau via Console:**

1. Go to EC2 → Launch Instance
2. **AMI**: Ubuntu 22.04 LTS (Deep Learning AMI recommended)
3. **Instance Type**: g4dn.xlarge
4. **Storage**: 100GB gp3 SSD
5. **Security Group**: Open ports 22, 80, 443, 5000
6. **Key Pair**: Create/Select existing

---

### Step 2: Configure Security Group

```bash
# Inbound Rules
- SSH (22) → Your IP
- HTTP (80) → 0.0.0.0/0
- HTTPS (443) → 0.0.0.0/0
- Custom TCP (5000) → 0.0.0.0/0 (API)
- Custom TCP (5173) → 0.0.0.0/0 (Dev Frontend)

# Outbound Rules
- All traffic → 0.0.0.0/0
```

---

### Step 3: Connect & Setup Server

```bash
# Connect via SSH
ssh -i your-key.pem ubuntu@<PUBLIC_IP>

# Update system
sudo apt update && sudo apt upgrade -y

# Install NVIDIA drivers (if not using Deep Learning AMI)
sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit

# Verify GPU
nvidia-smi
```

---

### Step 4: Install Dependencies

```bash
# Install required packages
sudo apt install -y \
    python3 python3-pip python3-venv \
    ffmpeg git curl wget \
    nginx certbot python3-certbot-nginx

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installations
python3 --version
node --version
ffmpeg -version
nvidia-smi
```

---

### Step 5: Clone & Setup Application

```bash
# Clone repository
cd /home/ubuntu
git clone https://github.com/YOUR_USERNAME/clipping.git
cd clipping

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Setup frontend
cd ../frontend
npm install
npm run build
```

---

### Step 6: Configure Application

```bash
# Create .env file
cd /home/ubuntu/clipping/backend
cp .env.example .env
nano .env
```

**Production .env Settings:**

```env
# ============================================
# PRODUCTION CONFIGURATION
# ============================================

# Transcription (GPU optimized)
TRANSCRIPTION_BACKEND=faster-whisper
FASTER_WHISPER_MODEL=large-v3
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16
FASTER_WHISPER_BEAM_SIZE=5

# Hybrid System
HYBRID_TRANSCRIPTION_ENABLED=true
CONFIDENCE_RETRY_THRESHOLD=0.7

# Groq API (Free backup)
GROQ_API_ENABLED=true
GROQ_API_KEY=your_groq_api_key_here

# Deep Learning
ENABLE_DEEP_LEARNING_VIDEO=true
YOLO_MODEL_SIZE=s

# Performance
MAX_CLIPS_PER_VIDEO=30
PROCESSING_CONCURRENCY=2

# Production mode
FLASK_ENV=production
```

---

### Step 7: Setup Systemd Services

**Backend Service:**

```bash
sudo nano /etc/systemd/system/clipper-backend.service
```

```ini
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable & Start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable clipper-backend
sudo systemctl start clipper-backend

# Check status
sudo systemctl status clipper-backend
sudo journalctl -u clipper-backend -f
```

---

### Step 8: Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/clipper
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend static files
    location / {
        root /home/ubuntu/clipping/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;

        # Long timeout for video processing
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;

        # Large file uploads
        client_max_body_size 5G;
    }

    # Clip downloads
    location /outputs {
        alias /home/ubuntu/clipping/backend/outputs;
        add_header Content-Disposition 'attachment';
    }
}
```

**Enable site:**

```bash
sudo ln -s /etc/nginx/sites-available/clipper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Step 9: Setup SSL with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com
```

---

### Step 10: Setup S3 for Storage (Optional but Recommended)

```bash
# Install AWS CLI
sudo apt install -y awscli

# Configure AWS
aws configure
# Enter: Access Key, Secret Key, Region

# Create S3 bucket
aws s3 mb s3://your-clipper-bucket --region ap-southeast-1
```

**Update backend untuk S3 storage** (akan saya buat file terpisah).

---

## 📈 OPTIMISASI PRODUCTION

### GPU Memory Management

```python
# Di config.py, tambahkan:
import torch
torch.cuda.empty_cache()

# Limit GPU memory
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
```

### Processing Queue dengan Redis

```bash
# Install Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install Python Redis
pip install redis celery
```

### Auto-scaling dengan AWS

```bash
# Create Launch Template
aws ec2 create-launch-template \
  --launch-template-name clipper-template \
  --version-description "v1" \
  --launch-template-data file://launch-template.json

# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name clipper-asg \
  --launch-template LaunchTemplateName=clipper-template,Version=1 \
  --min-size 1 \
  --max-size 5 \
  --desired-capacity 1 \
  --vpc-zone-identifier subnet-xxxxx
```

---

## 💰 COST ESTIMATION

### Development/Testing (g4dn.xlarge)

| Item          | Cost/Month      |
| ------------- | --------------- |
| EC2 (8h/day)  | ~$126           |
| EBS 100GB gp3 | ~$8             |
| Data Transfer | ~$10            |
| **Total**     | **~$144/month** |

### Production (24/7, g4dn.xlarge)

| Item          | Cost/Month      |
| ------------- | --------------- |
| EC2 (24/7)    | ~$378           |
| EBS 200GB gp3 | ~$16            |
| S3 Storage    | ~$23 (1TB)      |
| CloudFront    | ~$20            |
| Route 53      | ~$0.50          |
| **Total**     | **~$437/month** |

### Savings Tips:

1. **Reserved Instance**: Hemat 40-60% dengan 1-3 year commitment
2. **Spot Instance**: Hemat 70-90% untuk non-critical jobs
3. **Stop instance** saat tidak dipakai

---

## 🔒 SECURITY BEST PRACTICES

1. **IAM Roles**: Gunakan IAM roles, bukan access keys
2. **VPC**: Deploy di private subnet dengan NAT Gateway
3. **Secrets Manager**: Simpan API keys di Secrets Manager
4. **WAF**: Gunakan AWS WAF untuk protect ALB
5. **CloudWatch**: Monitor dan alerting

---

## 🔧 TROUBLESHOOTING

### CUDA Out of Memory

```bash
# Reduce model size
FASTER_WHISPER_MODEL=medium
YOLO_MODEL_SIZE=n

# Or upgrade instance
EC2: g4dn.xlarge → g4dn.2xlarge
```

### Slow Processing

```bash
# Check GPU usage
nvidia-smi -l 1

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics ...
```

### Connection Issues

```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Check nginx
sudo nginx -t
sudo systemctl status nginx
```

---

## 📋 QUICK COMMANDS

```bash
# Start all services
sudo systemctl start clipper-backend nginx

# Stop all services
sudo systemctl stop clipper-backend

# View logs
sudo journalctl -u clipper-backend -f

# Check GPU
nvidia-smi

# Restart services
sudo systemctl restart clipper-backend nginx
```

---

## 🚀 ONE-LINER SETUP SCRIPT

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/clipping/main/aws_setup.sh | bash
```

---

**Last Updated**: December 2024
**Tested On**: Ubuntu 22.04 LTS + g4dn.xlarge + NVIDIA T4
