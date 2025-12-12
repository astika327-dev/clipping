# 🚀 Cara Menjalankan AI Video Clipper

Panduan lengkap untuk menjalankan aplikasi AI Video Clipper di terminal Windows PowerShell.

---

## 📋 Prasyarat

Pastikan sudah terinstall:
- **Python 3.13+** (sudah terinstall)
- **Node.js dan npm** (untuk frontend)
- **FFmpeg** (untuk video processing)
- **Git** (opsional)

---

## ⚙️ Setup Awal (Hanya Sekali)

### 1. Install Dependencies Backend

```powershell
# Masuk ke direktori project
cd c:\proyek\clipping

# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Install openai-whisper dari vendor
cd backend
pip install -e vendor/openai-whisper

# Install semua dependencies lainnya
pip install Flask Flask-CORS opencv-python opencv-contrib-python scenedetect pydub torchaudio ffmpeg-python python-dotenv Werkzeug psutil faster-whisper

# Kembali ke root directory
cd ..
```

### 2. Install Dependencies Frontend

```powershell
# Masuk ke direktori frontend
cd frontend

# Install dependencies npm
npm install

# Kembali ke root directory
cd ..
```

---

## 🎬 Menjalankan Aplikasi

### Opsi 1: Menggunakan Script Otomatis

Gunakan file `start.bat` yang sudah tersedia:

```powershell
# Jalankan dari root directory
.\start.bat
```

### Opsi 2: Manual (Lebih Terkontrol)

#### A. Jalankan Backend

Buka terminal PowerShell pertama:

```powershell
# 1. Masuk ke root directory
cd c:\proyek\clipping

# 2. Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Masuk ke folder backend
cd backend

# 4. Jalankan Flask server
python app.py
```

**Output yang diharapkan:**
```
🔧 Running in DEVELOPMENT mode
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Backend sekarang berjalan di: **http://127.0.0.1:5000**

#### B. Jalankan Frontend

Buka terminal PowerShell kedua (jangan tutup terminal backend):

```powershell
# 1. Masuk ke root directory
cd c:\proyek\clipping

# 2. Masuk ke folder frontend
cd frontend

# 3. Jalankan Vite dev server
npm run dev
```

**Output yang diharapkan:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

Frontend sekarang berjalan di: **http://localhost:5173/**

---

## 🌐 Mengakses Aplikasi

1. Buka browser (Chrome, Firefox, Edge, dll)
2. Kunjungi: **http://localhost:5173/**
3. Upload video dan mulai clipping!

---

## 📥 Pilihan Input Video

Sekarang ada dua cara memasukkan video panjang ke dalam sistem:

1. **Upload File Lokal**
  - Drag & drop atau klik kotak unggah.
  - Format yang didukung: MP4, MOV, AVI, MKV (maks 2GB / 60 menit).
  - Proses upload berjalan melalui koneksi browser → backend.

2. **Import lewat Link YouTube**
  - Masukkan URL video (public / unlisted) pada kolom “Import langsung dari YouTube”.
  - Klik tombol **“Ambil dari YouTube”**.
  - Backend akan memakai `yt-dlp` untuk mengunduh langsung ke server GPU sehingga lebih stabil untuk file besar.
  - Setelah unduhan selesai, kartu “Video Uploaded” akan muncul dengan metadata judul/channel dari YouTube.

> Catatan: Batas durasi & ukuran tetap sama (60 menit, 2GB). Video private / premium tidak bisa diambil.

---

## 🛑 Menghentikan Aplikasi

### Menghentikan Backend
Di terminal backend, tekan: **Ctrl + C**

### Menghentikan Frontend
Di terminal frontend, tekan: **Ctrl + C**

---

## 🔧 Troubleshooting

### Backend Tidak Jalan

**Problem:** Error saat menjalankan `python app.py`

**Solusi:**
```powershell
# Pastikan venv aktif (terlihat (.venv) di awal prompt)
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies jika perlu
pip install -r backend/requirements.txt
```

### Frontend Tidak Jalan

**Problem:** Error saat `npm run dev`

**Solusi:**
```powershell
# Hapus node_modules dan reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

### FFmpeg Not Found

**Problem:** Error "FFmpeg not found"

**Solusi:**
1. Install FFmpeg via WinGet:
   ```powershell
   winget install Gyan.FFmpeg
   ```

2. Atau download manual dari: https://ffmpeg.org/download.html
3. Tambahkan ke PATH system

### Port Sudah Digunakan

**Problem:** Port 5000 atau 5173 sudah dipakai

**Solusi untuk Backend (Port 5000):**
```powershell
# Jalankan di port berbeda
python app.py --port 5001
```

**Solusi untuk Frontend:**
Edit `frontend/vite.config.js` dan ubah port:
```javascript
export default defineConfig({
  server: {
    port: 3000  // Ganti dengan port lain
  }
})
```

---

## 📊 Monitoring

### Cek Status Backend
```powershell
# Test API endpoint
Invoke-WebRequest -Uri http://127.0.0.1:5000/api/health
```

### Cek Resource Usage
Backend memiliki endpoint untuk monitoring:
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5000/api/system-stats
```

---

## 🔒 Mode Production

Untuk production deployment:

```powershell
# Backend Production
cd backend
python app.py --production --port 8000

# Frontend Build
cd frontend
npm run build

# Serve frontend static files melalui backend
# Files akan tersedia di backend/dist
```

---

## 📝 Variabel Environment (Opsional)

Buat file `.env` di folder `backend/` untuk kustomisasi:

```env
# Transcription Settings
TRANSCRIPTION_BACKEND=faster-whisper
WHISPER_MODEL=tiny
WHISPER_LANGUAGE=id
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8_float16
FASTER_WHISPER_BEAM_SIZE=1
FASTER_WHISPER_CHUNK_LENGTH=30

# Processing Settings
PROCESSING_CONCURRENCY=1
PROCESSING_COOLDOWN_SECONDS=2
EXPORT_THROTTLE_SECONDS=0.5

# Upload Limits
MAX_VIDEO_SIZE=2147483648  # 2GB in bytes
MAX_VIDEO_DURATION=3600    # 60 minutes
```

---

## 📁 Struktur Direktori

```
c:\proyek\clipping\
├── .venv/                    # Virtual environment Python
├── backend/                  # Flask backend
│   ├── app.py               # Main application
│   ├── config.py            # Configuration
│   ├── requirements.txt     # Python dependencies
│   ├── uploads/             # Video uploads (temporary)
│   ├── outputs/             # Generated clips
│   └── vendor/              # Local packages
├── frontend/                # React frontend
│   ├── src/                 # Source code
│   ├── package.json         # NPM dependencies
│   └── vite.config.js       # Vite configuration
└── start.bat                # Quick start script
```

---

## 🎯 Tips & Tricks

### 1. **Gunakan Model Whisper Lebih Besar untuk Akurasi Lebih Tinggi**
Edit `.env` atau `backend/config.py`:
```python
WHISPER_MODEL='small'  # atau 'medium', 'large'
```

### 2. **Proses Multiple Videos**
Set `PROCESSING_CONCURRENCY` lebih tinggi di `.env`:
```env
PROCESSING_CONCURRENCY=2
```

### 3. **Auto Caption**
Enable auto caption di UI atau API:
```json
{
  "auto_caption": true
}
```

### 4. **Monitoring Real-time**
Frontend memiliki ResourceMonitor component yang menampilkan:
- CPU usage
- Memory usage
- Python process stats
- Node process stats

---

## 🆘 Bantuan Lebih Lanjut

- **README.md** - Overview project
- **QUICKSTART.md** - Quick start guide
- **TESTING.md** - Testing guidelines
- **ALGORITHM.md** - Algorithm details
- **PROJECT_STRUCTURE.md** - Code structure

---

## ✅ Checklist Sebelum Mulai

- [ ] Python 3.13+ terinstall
- [ ] Virtual environment aktif
- [ ] Backend dependencies terinstall
- [ ] Node.js dan npm terinstall
- [ ] Frontend dependencies terinstall
- [ ] FFmpeg terinstall dan di PATH
- [ ] Port 5000 dan 5173 tersedia
- [ ] Minimal 4GB RAM tersedia

---

**🎉 Selamat! Aplikasi sudah siap digunakan.**

Jika ada masalah, cek section Troubleshooting atau buka issue di repository.

touch ~/.no_auto_tmux
exit