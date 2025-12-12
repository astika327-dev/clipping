#!/bin/bash
# ============================================
# Vast.ai GPU Server Setup Script
# AI Video Clipper - Automated Installation
# ============================================

set -e  # Exit on error

echo "🚀 Starting AI Video Clipper Setup on Vast.ai..."
echo "================================================="

# Step 1: Update system
echo ""
echo "📦 Step 1: Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install dependencies
echo ""
echo "🔧 Step 2: Installing dependencies..."
apt install -y git python3 python3-pip python3-venv ffmpeg curl wget nano

# Step 3: Clone repository
echo ""
echo "📥 Step 3: Cloning repository..."
cd ~
if [ -d "clipping" ]; then
    echo "   Repository already exists, pulling latest..."
    cd clipping
    git pull origin main
else
    git clone https://github.com/astika327-dev/clipping.git
    cd clipping
fi

# Step 4: Setup Python virtual environment
echo ""
echo "🐍 Step 4: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 5: Upgrade pip
echo ""
echo "⬆️ Step 5: Upgrading pip..."
pip install --upgrade pip

# Step 6: Install PyTorch with CUDA
echo ""
echo "🔥 Step 6: Installing PyTorch with CUDA support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Step 7: Install project dependencies
echo ""
echo "📚 Step 7: Installing project dependencies..."
cd backend
pip install -r requirements.txt

# Step 8: Install faster-whisper
echo ""
echo "🎤 Step 8: Installing faster-whisper..."
pip install faster-whisper

# Step 9: Create required folders
echo ""
echo "📁 Step 9: Creating required folders..."
mkdir -p uploads outputs
chmod 755 uploads outputs

# Step 10: Verify CUDA
echo ""
echo "🔍 Step 10: Verifying CUDA availability..."
python3 -c "import torch; print('✅ CUDA available:', torch.cuda.is_available()); print('   GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"

# Step 11: Verify FFmpeg
echo ""
echo "🎬 Step 11: Verifying FFmpeg..."
ffmpeg -version | head -1

# Done!
echo ""
echo "================================================="
echo "✅ Setup Complete!"
echo "================================================="
echo ""
echo "To start the backend server, run:"
echo "  source ~/clipping/venv/bin/activate"
echo "  cd ~/clipping/backend"
echo "  python app.py"
echo ""
echo "The server will be available at: http://localhost:5000"
echo ""
