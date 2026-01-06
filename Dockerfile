# ================================================
# AI Video Clipper - Docker GPU Image
# ================================================
# Build: docker build -t ai-video-clipper .
# Run:   docker run --gpus all -p 5000:5000 -p 80:80 ai-video-clipper
# ================================================

FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Jakarta

# System dependencies + cuDNN 9 for faster-whisper/ctranslate2
RUN apt-get update && apt-get install -y --allow-change-held-packages \
    python3 python3-pip python3-venv \
    ffmpeg git curl wget nano \
    nginx \
    libcudnn9-cuda-12 libcudnn9-dev-cuda-12 \
    && rm -rf /var/lib/apt/lists/*

# Disable Triton for OpenAI Whisper (fallback compatibility)
ENV WHISPER_TRITON=0

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy backend first for caching
COPY backend/requirements.txt /app/backend/
RUN pip3 install --no-cache-dir -r /app/backend/requirements.txt

# Install PyTorch with CUDA
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Copy frontend and build
COPY frontend/ /app/frontend/
WORKDIR /app/frontend
RUN npm install && npm run build

# Copy backend
COPY backend/ /app/backend/

# Create directories
RUN mkdir -p /app/backend/uploads /app/backend/outputs \
    && chmod 755 /app/backend/uploads /app/backend/outputs

# Configure Nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Environment variables
ENV FLASK_ENV=production
ENV TRANSCRIPTION_BACKEND=faster-whisper
ENV FASTER_WHISPER_DEVICE=cuda
ENV FASTER_WHISPER_COMPUTE_TYPE=float16
ENV FASTER_WHISPER_MODEL=large-v3
ENV ENABLE_DEEP_LEARNING_VIDEO=true

# Expose ports
EXPOSE 80 5000

# Working directory
WORKDIR /app/backend

# Start script
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
