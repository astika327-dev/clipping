#!/bin/bash
# ================================================
# Docker Container Start Script
# ================================================

echo "🚀 Starting AI Video Clipper..."

# Start Nginx in background
echo "📡 Starting Nginx..."
nginx

# Check CUDA availability
echo "🎮 Checking GPU..."
python3 -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU mode')" 2>/dev/null || echo "CPU mode (no GPU detected)"

# Start Flask backend (foreground)
echo "🔧 Starting Backend..."
cd /app/backend
python3 app.py --production --port 5000
