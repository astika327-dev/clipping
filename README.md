# 🎬 AI Video Clipper - TikTok Auto Clip Generator

Aplikasi otomatis yang menganalisis video panjang dan memotongnya menjadi klip-klip pendek yang menarik untuk TikTok, Reels, dan Shorts.

## 🎯 Fitur Utama

- ✅ Upload video panjang (MP4, MOV, AVI)
- ✅ Analisis audio dengan speech-to-text (Whisper)
- ✅ Deteksi scene change otomatis
- ✅ Deteksi wajah dan ekspresi
- ✅ Pemilihan klip berdasarkan:
  - Hook kuat di awal
  - Konten emosional tinggi
  - Punchline dan fakta menarik
  - Potensi viral
- ✅ Generate klip dengan durasi optimal (9-15s, 18-22s, 28-32s)
- ✅ Skor potensi viral untuk setiap klip
- ✅ Preview dan download klip

## 🛠️ Tech Stack

### Backend

- **Python 3.10+**
- **Flask** - Web framework
- **FFmpeg** - Video processing
- **OpenAI Whisper** - Speech-to-text
- **OpenCV** - Scene detection & face detection
- **scenedetect** - Advanced scene detection
- **pydub** - Audio processing

### Frontend

- **React + Vite** - Modern UI framework
- **TailwindCSS** - Styling
- **Axios** - HTTP client
- **React Player** - Video preview

## 📦 Instalasi

### Prerequisites

1. **Python 3.10+**
2. **Node.js 18+**
3. **FFmpeg** - [Download FFmpeg](https://ffmpeg.org/download.html)

### Backend Setup

```bash
# 1. Masuk ke folder backend
cd backend

# 2. Buat virtual environment
python -m venv venv

# 3. Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Download Whisper model (first run akan otomatis download)
# Model akan di-download saat pertama kali digunakan
```

### Frontend Setup

```bash
# 1. Masuk ke folder frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Build frontend (optional, untuk production)
npm run build
```

## 🚀 Cara Menjalankan

### Development Mode

**Terminal 1 - Backend:**

```bash
cd backend
venv\Scripts\activate  # Windows
python app.py
```

Backend akan berjalan di: `http://localhost:5000`

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

Frontend akan berjalan di: `http://localhost:5173`

### Production Mode

```bash
cd backend
venv\Scripts\activate
python app.py --production
```

Aplikasi akan serve frontend dari folder `frontend/dist` di `http://localhost:5000`

## 📖 Cara Menggunakan

1. **Buka aplikasi** di browser (`http://localhost:5173` untuk dev)
2. **Upload video** - Klik area upload atau drag & drop file video
3. **Atur pengaturan** (optional):
   - Target durasi klip
   - Gaya klip (lucu, edukasi, dramatis, opini)
   - Bahasa video
4. **Klik "Generate Clips"** - Tunggu proses analisis (bisa 2-10 menit tergantung durasi video)
5. **Preview hasil** - Lihat klip yang dihasilkan dengan skor viral
6. **Download klip** - Download per klip atau semua sekaligus

## 🧠 Algoritma Pemilihan Klip

### 1. Analisis Audio (Whisper)

- Transkripsi lengkap video
- Deteksi hook kuat (kalimat pembuka)
- Identifikasi punchline, fakta mengejutkan
- Analisis emosi dari kata-kata

### 2. Analisis Visual (OpenCV)

- Scene change detection
- Face detection & tracking
- Deteksi gerakan besar
- Identifikasi close-up speaker

### 3. Scoring System

Setiap segmen diberi skor berdasarkan:

- **Hook strength** (30%): Kalimat pembuka yang kuat
- **Content value** (25%): Informatif, lucu, atau emosional
- **Visual engagement** (20%): Wajah, gerakan, ekspresi
- **Pacing** (15%): Tidak ada jeda panjang
- **Ending impact** (10%): Punchline atau cliffhanger

### 4. Clip Selection

- Pilih top 5-10 segmen dengan skor tertinggi
- Filter durasi (9-15s, 18-22s, 28-32s)
- Pastikan setiap klip punya hook + isi + ending

### 5. Post-Processing

- Hapus silent/jeda panjang
- Trim filler words ("ehm", "anu", dll)
- Export dengan codec optimal untuk TikTok

## 📊 Output Format

Setiap klip menghasilkan:

```json
{
  "filename": "clip_001.mp4",
  "title": "Hard truth tentang bisnis",
  "start_time": "00:05:23",
  "end_time": "00:05:38",
  "duration": 15,
  "viral_score": "Tinggi",
  "reason": "Opini kontroversial + hook kuat di awal",
  "category": "opini",
  "transcript": "Ini yang gak pernah diomongin..."
}
```

## ⚙️ Konfigurasi

Edit `backend/config.py` untuk mengatur:

- `MAX_VIDEO_SIZE`: Ukuran maksimal upload (default: 2GB)
- `MAX_VIDEO_DURATION`: Durasi maksimal video (default: 60 menit)
- `TRANSCRIPTION_BACKEND`: `faster-whisper` (default) atau `openai-whisper`
- `FASTER_WHISPER_MODEL`: Model untuk faster-whisper (`tiny` default supaya hemat CPU/RAM; ganti ke `base`/`small` bila perlu akurasi lebih)
- `FASTER_WHISPER_BEAM_SIZE`: Default `1` untuk proses cepat; naikkan jika butuh akurasi ekstra
- `WHISPER_MODEL`: Model fallback openai-whisper (`tiny` default)
- `CLIP_DURATIONS`: Target durasi klip
- `MIN_VIRAL_SCORE`: Skor minimal untuk klip
- `PROCESSING_CONCURRENCY`: Jumlah job paralel (default `1` untuk laptop); tingkatkan hanya jika CPU/GPU kuat
- `PROCESSING_COOLDOWN_SECONDS`: Jeda antar job berat agar CPU bisa istirahat (default `2s`)
- `EXPORT_THROTTLE_SECONDS`: Delay antar export klip (default `0.5s`) supaya disk/CPU tidak spike

## 🔧 Troubleshooting

### FFmpeg not found

```bash
# Windows: Download dari https://ffmpeg.org/download.html
# Tambahkan ke PATH atau letakkan di folder backend/

# Linux:
sudo apt install ffmpeg

# Mac:
brew install ffmpeg
```

### Whisper model download gagal

```bash
# Manual download model
python -c "import whisper; whisper.load_model('base')"
```

### Memory error saat processing

- ⚠️ Face detection: Basic (OpenCV Haar Cascade)
- ⚠️ Processing time: ~2-10 menit per video

## 🎯 Roadmap v2.0

- [ ] Support lebih banyak bahasa
- [ ] Advanced emotion detection (AI model)
- [ ] Auto-generate captions/subtitles
- [ ] Background music suggestion
- [ ] Batch processing multiple videos
- [x] ~~Cloud deployment~~ ✅ AWS Ready!
- [ ] API untuk integrasi

## ☁️ AWS Cloud Deployment

Deploy ke AWS untuk processing lebih cepat dengan GPU!

### Quick Deploy Options:

| Method                                      | Time   | Complexity  |
| ------------------------------------------- | ------ | ----------- |
| [CloudFormation](./aws-cloudformation.yaml) | 10 min | ⭐ Easy     |
| [Shell Script](./aws_setup.sh)              | 15 min | ⭐⭐ Medium |
| [Docker](./docker-compose.yml)              | 5 min  | ⭐ Easy     |

### On-Demand (Hemat Biaya!)

Jalankan **hanya saat diperlukan** - hemat hingga 96%!

```powershell
# Setup sekali
cd aws-scripts
.\setup-aws.ps1

# Penggunaan harian
.\start-clipper.ps1   # Start instance
# ... gunakan aplikasi ...
.\stop-clipper.ps1    # Stop (PENTING!)
```

📖 **Guides:**

- [AWS Quick Start](./AWS_QUICKSTART.md) - Deploy dalam 10 menit
- [AWS Full Guide](./AWS_DEPLOYMENT.md) - Panduan lengkap
- [On-Demand Guide](./AWS_ONDEMAND.md) - Hemat biaya

## 📝 License

MIT License - Free to use and modify

## 🤝 Contributing

Pull requests welcome! Untuk perubahan besar, buka issue terlebih dahulu.

---

**Dibuat dengan ❤️ untuk content creators Indonesia**
