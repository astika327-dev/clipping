#!/bin/bash
exec > >(tee /var/log/user-data.log) 2>&1
echo "=== AI Video Clipper Setup - Budget Optimized ==="
echo "Start time: $(date)"

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y python3 python3-pip python3-venv ffmpeg git curl wget nginx

# Install NVIDIA drivers
apt-get install -y nvidia-driver-535 nvidia-cuda-toolkit

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Clone repository
cd /home/ubuntu
git clone https://github.com/astika327-dev/clipping.git
chown -R ubuntu:ubuntu clipping

# Setup Python
cd clipping
python3 -m venv venv
source venv/bin/activate

cd backend
pip install --upgrade pip
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Create optimized .env for budget
cat > .env << 'ENVFILE'
# ============================================
# AWS BUDGET OPTIMIZED CONFIGURATION ($119)
# ============================================

# === TRANSCRIPTION (Optimized for T4 GPU) ===
TRANSCRIPTION_BACKEND=faster-whisper
FASTER_WHISPER_MODEL=medium
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16
FASTER_WHISPER_BEAM_SIZE=3

# === HYBRID TRANSCRIPTION ===
HYBRID_TRANSCRIPTION_ENABLED=true
CONFIDENCE_RETRY_THRESHOLD=0.65
GROQ_API_ENABLED=true
GROQ_API_KEY=

# === LLM INTELLIGENCE ===
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile

# === DEEP LEARNING VIDEO ===
ENABLE_DEEP_LEARNING_VIDEO=true
YOLO_MODEL_SIZE=n
ENABLE_FACE_DETECTION=true
MEDIAPIPE_MODEL_COMPLEXITY=0

# === PERFORMANCE ===
MAX_CLIPS_PER_VIDEO=20
PROCESSING_CONCURRENCY=1
MAX_VIDEO_DURATION=3600
MAX_UPLOAD_SIZE=2147483648

# === GPU MEMORY ===
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256
CUDA_VISIBLE_DEVICES=0

# === AUTO-CLEANUP ===
AUTO_CLEANUP_ENABLED=true
CLEANUP_AGE_HOURS=24
ENVFILE

mkdir -p uploads outputs

# Build frontend
cd ../frontend
npm install
npm run build

# Setup systemd service
cat > /etc/systemd/system/clipper-backend.service << 'EOF'
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

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable clipper-backend
systemctl start clipper-backend

# Configure Nginx
cat > /etc/nginx/sites-available/clipper << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        root /home/ubuntu/clipping/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location ~ ^/(upload|process|status|download|clips|storage|system|health|youtube|api) {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        client_max_body_size 5G;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/clipper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "=== Setup Complete ==="
echo "End time: $(date)"
