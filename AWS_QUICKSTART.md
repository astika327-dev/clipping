# 🚀 AWS Quick Start Guide

Panduan cepat untuk deploy AI Video Clipper ke AWS dalam 10 menit.

---

## ⚡ QUICK START (3 Methods)

### Method 1: One-Click CloudFormation (Recommended)

```bash
# 1. Download template
curl -O https://raw.githubusercontent.com/astika327-dev/clipping/main/aws-cloudformation.yaml

# 2. Deploy via AWS CLI
aws cloudformation create-stack \
  --stack-name ai-video-clipper \
  --template-body file://aws-cloudformation.yaml \
  --parameters \
    ParameterKey=KeyName,ParameterValue=YOUR_KEY_PAIR \
    ParameterKey=InstanceType,ParameterValue=g4dn.xlarge \
  --capabilities CAPABILITY_NAMED_IAM

# 3. Wait for completion (5-10 minutes)
aws cloudformation wait stack-create-complete --stack-name ai-video-clipper

# 4. Get output URL
aws cloudformation describe-stacks \
  --stack-name ai-video-clipper \
  --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
  --output text
```

---

### Method 2: Shell Script Setup

```bash
# 1. Launch EC2 GPU instance (g4dn.xlarge, Ubuntu 22.04)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP

# 3. Run setup script
curl -fsSL https://raw.githubusercontent.com/astika327-dev/clipping/main/aws_setup.sh | bash

# 4. Access application
# http://YOUR_PUBLIC_IP
```

---

### Method 3: Docker (Fastest)

```bash
# 1. SSH into EC2 GPU instance
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP

# 2. Install Docker with GPU support
curl -fsSL https://get.docker.com | sh
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 3. Clone and run
git clone https://github.com/astika327-dev/clipping.git
cd clipping
docker-compose up -d

# 4. Access application
# http://YOUR_PUBLIC_IP
```

---

## 📊 Instance Comparison

| Instance        | GPU  | vRAM | Cost/hr | Best For               |
| --------------- | ---- | ---- | ------- | ---------------------- |
| **g4dn.xlarge** | T4   | 16GB | $0.526  | ✅ Most cost-effective |
| g4dn.2xlarge    | T4   | 16GB | $0.752  | Higher CPU workloads   |
| g5.xlarge       | A10G | 24GB | $1.006  | More GPU memory        |
| p3.2xlarge      | V100 | 16GB | $3.06   | Fastest processing     |

**Recommendation**: Start with **g4dn.xlarge**, upgrade if needed.

---

## 💰 Cost Estimation

| Usage Pattern        | Monthly Cost |
| -------------------- | ------------ |
| Dev/Testing (8h/day) | ~$130        |
| Production (24/7)    | ~$400        |
| Reserved (1-year)    | ~$240        |
| Spot Instance        | ~$50-80      |

---

## 🔧 Post-Setup

### 1. Configure Domain (Optional)

```bash
# Point domain to Elastic IP, then:
sudo certbot --nginx -d your-domain.com
```

### 2. Add Groq API Key (Recommended)

```bash
echo "GROQ_API_KEY=your_key_here" >> ~/clipping/backend/.env
sudo systemctl restart clipper-backend
```

### 3. Setup YouTube Cookies

```bash
nano ~/clipping/backend/youtube_cookies.txt
# Paste cookies content, save
```

---

## 🛠️ Useful Commands

```bash
# Check status
sudo systemctl status clipper-backend

# View logs
sudo journalctl -u clipper-backend -f

# Restart service
sudo systemctl restart clipper-backend

# Check GPU
nvidia-smi

# Check disk space
df -h
```

---

## 🔗 Access Points

After deployment:

- **Frontend**: `http://YOUR_PUBLIC_IP`
- **API**: `http://YOUR_PUBLIC_IP/api`
- **Health Check**: `http://YOUR_PUBLIC_IP/health`

---

**Need help?** Open an issue on GitHub or check the full [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) guide.
