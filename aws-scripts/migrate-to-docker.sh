#!/bin/bash
# ================================================
# Migrate Existing Instance to Docker
# ================================================
# Run this script on your existing EC2 instance
# to switch from manual deployment to Docker
# ================================================

set -e

echo "================================================"
echo "   Migrating AI Video Clipper to Docker"
echo "================================================"
echo ""

# === Step 1: Stop existing services ===
echo "🛑 Step 1: Stopping existing services..."
sudo systemctl stop clipper-backend 2>/dev/null || true
sudo systemctl disable clipper-backend 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true
echo "   ✅ Services stopped"

# === Step 2: Install Docker ===
echo ""
echo "🐳 Step 2: Installing Docker..."

# Remove old Docker versions
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to docker group
sudo usermod -aG docker $USER

echo "   ✅ Docker installed"

# === Step 3: Install NVIDIA Container Toolkit ===
echo ""
echo "🎮 Step 3: Installing NVIDIA Container Toolkit..."

# Add NVIDIA repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo "   ✅ NVIDIA Container Toolkit installed"

# === Step 4: Setup Docker deployment directory ===
echo ""
echo "📁 Step 4: Setting up deployment directory..."

mkdir -p ~/clipper-docker/data/{uploads,outputs}

# Copy existing .env if exists
if [ -f ~/clipping/backend/.env ]; then
    cp ~/clipping/backend/.env ~/clipper-docker/.env
    echo "   ✅ Copied existing .env"
else
    # Create default .env
    cat > ~/clipper-docker/.env << 'ENVFILE'
# ============================================
# AWS DOCKER CONFIGURATION
# ============================================

TRANSCRIPTION_BACKEND=faster-whisper
FASTER_WHISPER_MODEL=medium
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16
FASTER_WHISPER_BEAM_SIZE=3

HYBRID_TRANSCRIPTION_ENABLED=true
CONFIDENCE_RETRY_THRESHOLD=0.65
GROQ_API_ENABLED=true
GROQ_API_KEY=

LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile

ENABLE_DEEP_LEARNING_VIDEO=true
YOLO_MODEL_SIZE=n
ENABLE_FACE_DETECTION=true
MEDIAPIPE_MODEL_COMPLEXITY=0

MAX_CLIPS_PER_VIDEO=20
PROCESSING_CONCURRENCY=1
MAX_VIDEO_DURATION=3600
MAX_UPLOAD_SIZE=2147483648

PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256
CUDA_VISIBLE_DEVICES=0

AUTO_CLEANUP_ENABLED=true
CLEANUP_AGE_HOURS=24
ENVFILE
    echo "   ✅ Created default .env"
fi

# Create docker-compose.yml
cat > ~/clipper-docker/docker-compose.yml << 'COMPOSE'
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

echo "   ✅ docker-compose.yml created"

# Create helper scripts
cat > ~/clipper-docker/update.sh << 'UPDATE'
#!/bin/bash
cd ~/clipper-docker
docker compose pull
docker compose up -d
docker system prune -f
echo "✅ Updated to latest image"
UPDATE
chmod +x ~/clipper-docker/update.sh

cat > ~/clipper-docker/logs.sh << 'LOGS'
#!/bin/bash
docker logs -f ai-video-clipper
LOGS
chmod +x ~/clipper-docker/logs.sh

cat > ~/clipper-docker/restart.sh << 'RESTART'
#!/bin/bash
cd ~/clipper-docker
docker compose restart
echo "✅ Containers restarted"
RESTART
chmod +x ~/clipper-docker/restart.sh

echo "   ✅ Helper scripts created"

# === Step 5: Instructions ===
echo ""
echo "================================================"
echo "   ✅ MIGRATION COMPLETE!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. LOGIN to GitHub Container Registry:"
echo "   echo 'YOUR_GITHUB_TOKEN' | docker login ghcr.io -u astika327-dev --password-stdin"
echo ""
echo "2. PULL and START the container:"
echo "   cd ~/clipper-docker"
echo "   docker compose pull"
echo "   docker compose up -d"
echo ""
echo "3. CHECK status:"
echo "   docker ps"
echo "   docker logs -f ai-video-clipper"
echo ""
echo "Helper scripts available in ~/clipper-docker/:"
echo "   ./update.sh   - Pull latest image and restart"
echo "   ./logs.sh     - View container logs"
echo "   ./restart.sh  - Restart containers"
echo ""
echo "Old installation in ~/clipping can be deleted later if everything works."
echo ""
