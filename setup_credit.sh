#!/bin/bash
exec > >(tee /var/log/user-data.log) 2>&1
echo "=== CREDIT TIER SETUP (HIGH PERF) ==="

# 100GB Disk is enough, but 4GB swap is still good for stability
fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

apt-get update && apt-get install -y python3-pip python3-venv ffmpeg git nginx nodejs npm

# Install NodeJS 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs

cd /home/ubuntu
git clone https://github.com/astika327-dev/clipping.git
chown -R ubuntu:ubuntu clipping
cd clipping/backend

# Virtual Env
python3 -m venv venv
source venv/bin/activate

# Install Full PyTorch (CPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install All Requirements
pip install -r requirements.txt

# Config .env
cp .env.example .env
cat >> .env <<EOT

# === CREDIT TIER OVERRIDES ===
TRANSCRIPTION_BACKEND=faster-whisper
WHISPER_MODEL=medium
FASTER_WHISPER_MODEL=medium
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
ENABLE_DEEP_LEARNING_VIDEO=true
YOLO_MODEL_SIZE=n
GROQ_API_ENABLED=true
USE_GPU_ACCELERATION=false
VIDEO_CODEC=libx264
NVENC_PRESET=faster
PROCESSING_CONCURRENCY=2
EOT

mkdir -p uploads outputs

# Build Frontend
cd ../frontend && npm install && npm run build

# Nginx & Systemd
cat > /etc/systemd/system/clipper-backend.service << 'EOF'
[Unit]
Description=Backend
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/clipping/backend
Environment="PATH=/home/ubuntu/clipping/venv/bin:/usr/bin"
ExecStart=/home/ubuntu/clipping/venv/bin/python app.py --production --port 5000
Restart=always
[Install]
WantedBy=multi-user.target
EOF

systemctl enable clipper-backend && systemctl start clipper-backend

cat > /etc/nginx/sites-available/clipper << 'NGINX'
server {
    listen 80;
    location / { root /home/ubuntu/clipping/frontend/dist; try_files $uri $uri/ /index.html; }
    location ~ ^/(upload|process|status|download|clips|storage|system|health|youtube|api) {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        client_max_body_size 10G;
        proxy_read_timeout 900;
        send_timeout 900;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/clipper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
