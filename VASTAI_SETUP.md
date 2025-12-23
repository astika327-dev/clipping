# 🚀 Vast.ai GPU Server Setup Guide

Panduan lengkap untuk deploy AI Video Clipper di Vast.ai GPU server.

## 📋 Prerequisites

- SSH client (built-in di Windows PowerShell/Terminal)
- Vast.ai instance sudah running

## 🔗 Step 1: Connect ke Server

**SSH dengan Port Forwarding (Backend + Frontend):**

```bash
ssh -p 50950 root@171.101.230.251 -L 5000:localhost:5000 -L 5173:localhost:5173
```

**Atau backend saja:**

```bash
ssh -p 50950 root@171.101.230.251 -L 5000:localhost:5000
```

> **Port Forwarding:**
>
> - `-L 5000:localhost:5000` → Backend API (Flask)
> - `-L 5173:localhost:5173` → Frontend (Vite)
>
> Setelah server running, akses dari browser lokal:
>
> - Backend: http://localhost:5000
> - Frontend: http://localhost:5173

---

## 📦 Step 2: Update System & Install Dependencies

```bash
# Update package list
apt update && apt upgrade -y

# Install essential tools
apt install -y git python3 python3-pip python3-venv ffmpeg curl wget nano

# Verify installations
python3 --version
ffmpeg -version
git --version
```

---

## 📥 Step 3: Clone Repository

```bash
# Navigate to home or workspace
cd ~

# Clone the repository
git clone https://github.com/astika327-dev/clipping.git

# Enter the project directory
cd clipping
```

---

## 🐍 Step 4: Setup Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

---

## 📚 Step 5: Install Python Dependencies

```bash
# Navigate to backend
cd backend

# Install requirements
pip install -r requirements.txt
```

> ⚠️ **Note:** Vast.ai instances sudah pre-installed dengan PyTorch + CUDA. **TIDAK perlu install PyTorch lagi!**

### Jika ada error dengan PyTorch/CUDA (jarang terjadi):

```bash
# Hanya jika PyTorch tidak terdeteksi (sangat jarang di Vast.ai)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Install faster-whisper dengan GPU support:

```bash
pip install faster-whisper
```

---

## ⚙️ Step 6: Configure for GPU

```bash
# Check if CUDA is available
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
```

### Edit config jika perlu:

```bash
nano config.py
```

Pastikan settings ini untuk GPU:

```python
FASTER_WHISPER_DEVICE = 'cuda'
FASTER_WHISPER_COMPUTE_TYPE = 'float16'
USE_GPU_ACCELERATION = True
```

### Jika muncul error `libcudnn_ops.so`

Instance Vast.ai biasanya sudah menyertakan CUDA + cuDNN, tetapi beberapa image minimal tidak memaketkan pustaka cuDNN 9.1 yang dibutuhkan oleh PyTorch/Faster-Whisper (mis. pesan `Unable to load any of libcudnn_ops.so...`). Cara tercepat untuk memasangnya:

```bash
# Download cuDNN 9.1 untuk CUDA 12.1
cd /tmp



# Ekstrak dan copy ke lokasi CUDA default
tar -xJf cudnn-linux-x86_64-9.1.0.70_cuda12.1-archive.tar.xz
sudo cp cudnn-linux-x86_64-9.1.0.70_cuda12.1-archive/include/cudnn*.h /usr/local/cuda/include/
sudo cp cudnn-linux-x86_64-9.1.0.70_cuda12.1-archive/lib/libcudnn* /usr/local/cuda/lib64/
sudo chmod a+r /usr/local/cuda/include/cudnn*.h /usr/local/cuda/lib64/libcudnn*
sudo ldconfig

# Verifikasi
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0))"
```

Setelah selesai, restart backend (`pkill -f "python app.py" && python app.py`) supaya Faster-Whisper memuat ulang cuDNN.

---

## 📁 Step 7: Create Required Folders

```bash
# Make sure you're in backend folder
cd ~/clipping/backend

# Create upload and output folders
mkdir -p uploads outputs

# Set permissions
chmod 755 uploads outputs
```

---

## 🍪 Step 8: Setup YouTube Cookies (Optional)

Jika ingin download dari YouTube, transfer file cookies:

**Dari PC lokal (buka terminal baru):**

```bash
scp -P 50950 c:\proyek\clipping\backend\youtube_cookies.txt root@171.101.230.251:~/clipping/backend/
```

**Atau buat manual di server:**

```bash
nano ~/clipping/backend/youtube_cookies.txt
# Paste isi cookies, lalu Ctrl+X, Y, Enter untuk save
```

---

## 🚀 Step 9: Run Backend Server

```bash
# Make sure virtual environment is activated
source ~/clipping/venv/bin/activate

# Navigate to backend
cd ~/clipping/backend

# Run the server (bind to all interfaces for remote access)
python app.py
```

Atau untuk production dengan custom host/port:

```bash
# Edit app.py untuk bind ke 0.0.0.0
# Atau gunakan environment variable:
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
python app.py
```

---

## 🌐 Step 10: Setup Frontend (Optional - untuk testing)

```bash
# Buka terminal baru dan SSH lagi
ssh -p 50950 root@171.101.230.251 -L 5173:localhost:5173

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Navigate to frontend
cd ~/clipping/frontend

# Install dependencies
npm install

# Run frontend dev server
npm run dev -- --host 0.0.0.0
```

---

## 🔧 Quick Commands Reference

### Start Backend:

```bash
source /workspace/clipping/venv/bin/activate && cd /workspace/clipping/backend && python app.py
```

### Start Frontend:

```bash
cd ~/clipping/frontend && npm run dev -- --host 0.0.0.0
```

### Check GPU Status:

```bash
nvidia-smi
```

### Check Python GPU:

```bash
source ~/clipping/venv/bin/activate
python3 -c "import torch; print(torch.cuda.is_available())"
```

### View Logs:

```bash
# Real-time log
tail -f ~/clipping/backend/app.log
```

---

## 🔥 Troubleshooting

### "CUDA out of memory"

```bash
# Reduce batch size di config.py
MAX_PARALLEL_EXPORTS = 1
FASTER_WHISPER_MODEL = 'base'  # Use smaller model
```

### "Module not found"

```bash
source ~/clipping/venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied"

```bash
chmod -R 755 ~/clipping
```

### "FFmpeg not found"

```bash
apt install -y ffmpeg
which ffmpeg
```

### Port already in use

```bash
# Find process using port
lsof -i :5000
# Kill it
kill -9 <PID>
```

---

## 📡 Akses dari PC Lokal

Setelah server berjalan dengan SSH port forwarding:

- **Backend API**: http://localhost:5000
- **Frontend**: http://localhost:5173

---

## 🛑 Stop Server

```bash
# Di terminal server
Ctrl + C

# Atau kill process
pkill -f "python app.py"
```

---

## 💾 Backup Clips

**Download hasil clips ke PC lokal:**

```bash
# Dari PowerShell lokal
scp -P 50950 -r root@171.101.230.251:~/clipping/backend/outputs/ C:\Users\YourName\Downloads\clips\
```

---

**Last Updated**: 2025-12-13
pip install mediapipe

pip install --upgrade mediapipe
