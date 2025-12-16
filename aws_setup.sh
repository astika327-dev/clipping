#!/bin/bash
# ================================================
# AI Video Clipper - AWS EC2 GPU Setup Script
# ================================================
# Run this script on a fresh EC2 GPU instance
# Recommended: g4dn.xlarge with Ubuntu 22.04 LTS
# ================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "================================================"
echo "   AI Video Clipper - AWS Setup Script"
echo "================================================"
echo -e "${NC}"

# Configuration
APP_DIR="/home/ubuntu/clipping"
REPO_URL="https://github.com/astika327-dev/clipping.git"
DOMAIN=""  # Set your domain here

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Step: $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# ================================================
# STEP 1: System Update
# ================================================
print_step "1/10 - System Update"

sudo apt update && sudo apt upgrade -y
print_status "System updated"

# ================================================
# STEP 2: Install System Dependencies
# ================================================
print_step "2/10 - Install System Dependencies"

sudo apt install -y \
    python3 python3-pip python3-venv \
    ffmpeg git curl wget nano htop \
    nginx certbot python3-certbot-nginx \
    redis-server

print_status "System dependencies installed"

# ================================================
# STEP 3: Verify/Install NVIDIA Drivers
# ================================================
print_step "3/10 - Verify NVIDIA GPU"

if command -v nvidia-smi &> /dev/null; then
    print_status "NVIDIA driver detected"
    nvidia-smi
else
    print_warning "Installing NVIDIA drivers..."
    sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit
    print_status "NVIDIA drivers installed (reboot required)"
fi

# ================================================
# STEP 4: Install Node.js
# ================================================
print_step "4/10 - Install Node.js"

curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

print_status "Node.js $(node --version) installed"

# ================================================
# STEP 5: Clone Repository
# ================================================
print_step "5/10 - Clone Repository"

if [ -d "$APP_DIR" ]; then
    print_warning "Directory exists, pulling latest..."
    cd $APP_DIR
    git pull
else
    git clone $REPO_URL $APP_DIR
fi

print_status "Repository cloned to $APP_DIR"

# ================================================
# STEP 6: Setup Python Environment
# ================================================
print_step "6/10 - Setup Python Virtual Environment"

cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
cd backend
pip install -r requirements.txt

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

print_status "Python environment configured"

# Verify CUDA
python3 -c "import torch; print('CUDA Available:', torch.cuda.is_available())"

# ================================================
# STEP 7: Setup Frontend
# ================================================
print_step "7/10 - Build Frontend"

cd $APP_DIR/frontend
npm install
npm run build

print_status "Frontend built successfully"

# ================================================
# STEP 8: Create Environment File
# ================================================
print_step "8/10 - Configure Environment"

cd $APP_DIR/backend

if [ ! -f .env ]; then
    cp .env.example .env
    
    # Update for production
    sed -i 's/FASTER_WHISPER_MODEL=large/FASTER_WHISPER_MODEL=large-v3/' .env
    sed -i 's/FASTER_WHISPER_DEVICE=cuda/FASTER_WHISPER_DEVICE=cuda/' .env
    sed -i 's/ENABLE_DEEP_LEARNING_VIDEO=true/ENABLE_DEEP_LEARNING_VIDEO=true/' .env
    
    print_status ".env file created"
else
    print_warning ".env file already exists, skipping..."
fi

# Create required directories
mkdir -p uploads outputs
chmod 755 uploads outputs

print_status "Directories configured"

# ================================================
# STEP 9: Setup Systemd Service
# ================================================
print_step "9/10 - Configure Systemd Service"

sudo tee /etc/systemd/system/clipper-backend.service > /dev/null <<EOF
[Unit]
Description=AI Video Clipper Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/venv/bin:/usr/bin"
ExecStart=$APP_DIR/venv/bin/python app.py --production --port 5000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable clipper-backend
sudo systemctl start clipper-backend

print_status "Systemd service configured and started"

# ================================================
# STEP 10: Configure Nginx
# ================================================
print_step "10/10 - Configure Nginx"

# Get public IP if no domain
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

sudo tee /etc/nginx/sites-available/clipper > /dev/null <<EOF
server {
    listen 80;
    server_name $PUBLIC_IP;

    # Frontend static files
    location / {
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
        
        # Long timeout for video processing
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        
        # Large file uploads
        client_max_body_size 5G;
    }

    # Direct API access (without /api prefix)
    location ~ ^/(upload|process|status|download|clips|storage|system|health) {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        client_max_body_size 5G;
    }

    # Clip downloads & previews
    location /outputs {
        alias $APP_DIR/backend/outputs;
        add_header Content-Disposition 'attachment';
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/clipper /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

print_status "Nginx configured"

# ================================================
# Enable Redis
# ================================================
sudo systemctl enable redis-server
sudo systemctl start redis-server

# ================================================
# Summary
# ================================================
echo -e "\n${GREEN}"
echo "================================================"
echo "   🎉 Setup Complete!"
echo "================================================"
echo -e "${NC}"

echo -e "${BLUE}Access your application:${NC}"
echo -e "  🌐 Frontend: http://$PUBLIC_IP"
echo -e "  🔧 Backend:  http://$PUBLIC_IP:5000"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  📊 Check status:  sudo systemctl status clipper-backend"
echo -e "  📝 View logs:     sudo journalctl -u clipper-backend -f"
echo -e "  🔄 Restart:       sudo systemctl restart clipper-backend"
echo -e "  🎮 GPU status:    nvidia-smi"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Configure domain in Nginx"
echo -e "  2. Setup SSL: sudo certbot --nginx -d your-domain.com"
echo -e "  3. Update .env with your Groq API key"
echo ""
echo -e "${GREEN}Happy clipping! 🎬${NC}"
