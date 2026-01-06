#!/bin/bash
# ================================================
# AI Video Clipper - Docker AWS Setup Script
# ================================================
# User data script untuk EC2 GPU instance dengan Docker
# ================================================

exec > >(tee /var/log/user-data.log) 2>&1
echo "=== AI Video Clipper Docker Setup ==="
echo "Start time: $(date)"

# === CONFIGURATION ===
GITHUB_USER="astika327-dev"
IMAGE_NAME="ghcr.io/${GITHUB_USER}/clipping:latest"
# Token akan di-inject saat deploy atau via Secrets Manager
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
echo "=== Installing Docker ==="
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install NVIDIA Driver
echo "=== Installing NVIDIA Driver ==="
apt-get install -y nvidia-driver-535

# Install NVIDIA Container Toolkit
echo "=== Installing NVIDIA Container Toolkit ==="
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Create app directory
mkdir -p /home/ubuntu/clipper/data/{uploads,outputs}
chown -R ubuntu:ubuntu /home/ubuntu/clipper

# Create docker-compose for deployment
cat > /home/ubuntu/clipper/docker-compose.yml << 'COMPOSE'
version: "3.8"

services:
  clipper:
    image: ghcr.io/astika327-dev/clipping:latest
    container_name: ai-video-clipper
    restart: unless-stopped
    ports:
      - "80:80"
      - "5000:5000"
    volumes:
      - ./data/uploads:/app/backend/uploads
      - ./data/outputs:/app/backend/outputs
      - ./.env:/app/backend/.env:ro
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:alpine
    container_name: clipper-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data

volumes:
  redis-data:

networks:
  default:
    name: clipper-network
COMPOSE

# Create default .env
cat > /home/ubuntu/clipper/.env << 'ENVFILE'
# ============================================
# AWS DOCKER CONFIGURATION
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

chown ubuntu:ubuntu /home/ubuntu/clipper/.env
chown ubuntu:ubuntu /home/ubuntu/clipper/docker-compose.yml

# Create systemd service for docker-compose
cat > /etc/systemd/system/clipper-docker.service << 'SERVICE'
[Unit]
Description=AI Video Clipper Docker
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/clipper
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu
Group=docker

[Install]
WantedBy=multi-user.target
SERVICE

# Login to GitHub Container Registry (if token provided)
if [ -n "$GITHUB_TOKEN" ]; then
    echo "=== Logging into GHCR ==="
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u astika327-dev --password-stdin
    
    # Pull the image
    echo "=== Pulling Docker Image ==="
    docker pull $IMAGE_NAME
    
    # Start the container
    cd /home/ubuntu/clipper
    docker compose up -d
    
    systemctl daemon-reload
    systemctl enable clipper-docker
else
    echo "=== GITHUB_TOKEN not provided ==="
    echo "To pull private image, run these commands manually:"
    echo "  echo YOUR_TOKEN | docker login ghcr.io -u astika327-dev --password-stdin"
    echo "  cd /home/ubuntu/clipper && docker compose up -d"
fi

# Create helper scripts
cat > /home/ubuntu/clipper/update.sh << 'UPDATE'
#!/bin/bash
# Update to latest image
cd /home/ubuntu/clipper
docker compose pull
docker compose up -d
docker system prune -f
UPDATE
chmod +x /home/ubuntu/clipper/update.sh

cat > /home/ubuntu/clipper/logs.sh << 'LOGS'
#!/bin/bash
# View container logs
docker logs -f ai-video-clipper
LOGS
chmod +x /home/ubuntu/clipper/logs.sh

chown -R ubuntu:ubuntu /home/ubuntu/clipper

echo "=== Docker Setup Complete ==="
echo "End time: $(date)"
echo ""
echo "To check container status: docker ps"
echo "To view logs: docker logs -f ai-video-clipper"
