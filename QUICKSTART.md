# ⚡ Quick Start Guide

Panduan cepat untuk menjalankan AI Video Clipper dalam 5 menit!

## 📋 Prerequisites

Pastikan sudah terinstall:

- ✅ Python 3.10 atau lebih baru
- ✅ Node.js 18 atau lebih baru
- ✅ FFmpeg ([Download di sini](https://ffmpeg.org/download.html))

## 🚀 Instalasi Cepat

### 1. Clone/Download Project

```bash
cd c:\proyek\clipping
```

### 2. Setup Backend (Terminal 1)

```bash
# Masuk ke folder backend
cd backend

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Jalankan server
python app.py
```

✅ Backend sekarang berjalan di `http://localhost:5000`

### 3. Setup Frontend (Terminal 2)

```bash
# Masuk ke folder frontend
cd frontend

# Install dependencies
npm install

# Jalankan dev server
npm run dev
```

✅ Frontend sekarang berjalan di `http://localhost:5173`

### 4. Buka Aplikasi

Buka browser dan akses: **http://localhost:5173**

## 🎬 Cara Menggunakan

### Step 1: Upload Video

1. Drag & drop video atau klik untuk pilih file
2. Tunggu upload selesai
3. Lihat info video (ukuran, durasi)

### Step 2: Atur Pengaturan

1. **Bahasa**: Pilih bahasa video (Indonesia/English)
2. **Durasi**: Pilih durasi klip yang diinginkan
   - Short: 9-15 detik
   - Medium: 18-22 detik
   - Long: 28-32 detik
   - All: Semua durasi
3. **Gaya**: Pilih gaya konten
   - Seimbang: Mix semua gaya
   - Lucu: Prioritas konten menghibur
   - Edukasi: Prioritas konten informatif
   - Dramatis: Prioritas konten emosional
   - Opini Keras: Prioritas konten kontroversial

### Step 3: Generate Klip

1. Klik tombol **"Generate Klip Sekarang"**
2. Tunggu proses selesai (2-10 menit tergantung durasi video)
3. Monitor progress bar

### Step 4: Download Klip

1. Preview klip dengan hover mouse
2. Klik klip untuk lihat detail
3. Download individual atau semua sekaligus

## 🎯 Tips Mendapatkan Hasil Terbaik

### ✅ Video yang Cocok

- Video dengan dialog/narasi yang jelas
- Video podcast, tutorial, review, vlog
- Durasi 5-30 menit (optimal)
- Audio yang jelas (tidak berisik)

### ❌ Video yang Kurang Cocok

- Video tanpa audio/dialog
- Video dengan musik saja
- Video dengan audio berisik
- Video terlalu pendek (< 3 menit)

### 💡 Rekomendasi Pengaturan

**Untuk Video Edukasi/Tutorial:**

- Bahasa: Sesuai video
- Durasi: Medium (18-22s)
- Gaya: Edukasi

**Untuk Video Entertainment:**

- Bahasa: Sesuai video
- Durasi: Short (9-15s)
- Gaya: Lucu

**Untuk Video Podcast/Interview:**

- Bahasa: Sesuai video
- Durasi: All
- Gaya: Seimbang

**Untuk Video Opini/Rant:**

- Bahasa: Sesuai video
- Durasi: Medium (18-22s)
- Gaya: Opini Keras

## ⚠️ Troubleshooting Cepat

### "FFmpeg not found"

```bash
# Download FFmpeg dari https://ffmpeg.org/download.html
# Extract dan tambahkan ke PATH
# Atau copy ffmpeg.exe ke folder backend/
```

### "Module not found" (Python)

```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### "Module not found" (Node)

```bash
cd frontend
npm install
```

### YouTube memerlukan cookie/login

YouTube kini memerlukan autentikasi untuk beberapa video. Ada 2 cara setup:

**Cara 1: Export cookies ke file (Recommended)**

1. Install browser extension "[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)"
2. Buka YouTube dan pastikan sudah login
3. Klik extension dan pilih "Export" → simpan sebagai `youtube_cookies.txt`
4. Set environment variable sebelum menjalankan backend:
   ```bash
   set YTDLP_COOKIES_FILE=C:\path\to\youtube_cookies.txt
   python app.py
   ```

**Cara 2: Gunakan cookies dari browser langsung**

1. Tutup browser (Chrome/Firefox/Edge) terlebih dahulu
2. Set environment variable:
   ```bash
   set YTDLP_COOKIES_FROM_BROWSER=chrome
   python app.py
   ```
   (Ganti `chrome` dengan `firefox`, `edge`, `opera`, atau `brave` sesuai browser yang dipakai)

### Klip terlalu pendek untuk video panjang (>1 jam)

Jika video podcast >1 jam menghasilkan klip terlalu pendek:

1. Pastikan menggunakan versi terbaru aplikasi
2. Sistem sekarang secara otomatis mendeteksi video panjang dan membuat segmen yang lebih panjang
3. Video >1 jam akan menghasilkan minimal 10 klip
4. Video >2 jam akan menghasilkan minimal 20 klip

### Processing terlalu lama

- Gunakan video lebih pendek (<15 menit)
- Edit `backend/config.py`:
  ```python
  WHISPER_MODEL = 'tiny'  # Lebih cepat
  ```

### Tidak ada klip yang dihasilkan

- Video mungkin tidak punya dialog yang cukup
- Coba video lain dengan narasi yang lebih jelas
- Turunkan `MIN_VIRAL_SCORE` di `backend/config.py`

## 📊 Estimasi Waktu Proses

| Durasi Video | Waktu Proses | Jumlah Klip |
| ------------ | ------------ | ----------- |
| 5 menit      | 2-3 menit    | 3-5 klip    |
| 10 menit     | 4-6 menit    | 5-8 klip    |
| 15 menit     | 6-10 menit   | 7-10 klip   |
| 30 menit     | 12-20 menit  | 10-15 klip  |
| 60 menit     | 25-40 menit  | 10-20 klip  |
| 2+ jam       | 50-90 menit  | 20-30 klip  |

## 🎓 Belajar Lebih Lanjut

- 📖 [README.md](README.md) - Dokumentasi lengkap
- 🧪 [TESTING.md](TESTING.md) - Panduan testing
- 🧠 [ALGORITHM.md](ALGORITHM.md) - Penjelasan algoritma

## 🆘 Butuh Bantuan?

Jika ada masalah:

1. Check terminal untuk error messages
2. Baca [TESTING.md](TESTING.md) untuk troubleshooting
3. Buka issue di GitHub

---

**Selamat mencoba! 🚀**
