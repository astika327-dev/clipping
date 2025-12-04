# 🧪 Testing Guide - AI Video Clipper

## Cara Test Aplikasi

### 1. Persiapan Video Test

Untuk testing, gunakan video dengan karakteristik berikut:

- **Durasi**: 5-15 menit (untuk testing cepat)
- **Konten**: Video dengan dialog/narasi yang jelas
- **Format**: MP4 (paling kompatibel)
- **Ukuran**: < 500MB (untuk testing cepat)

**Contoh video yang bagus untuk testing:**

- Video podcast
- Video tutorial/edukasi
- Video storytelling
- Video review produk
- Video vlog dengan narasi

### 2. Testing Backend

```bash
# 1. Masuk ke folder backend
cd backend

# 2. Aktifkan virtual environment
venv\Scripts\activate  # Windows
# atau
source venv/bin/activate  # Linux/Mac

# 3. Test health check
python -c "import requests; print(requests.get('http://localhost:5000/api/health').json())"

# 4. Jalankan server
python app.py
```

**Expected Output:**

```
🔧 Running in DEVELOPMENT mode
 * Running on http://127.0.0.1:5000
```

### 3. Testing Frontend

```bash
# 1. Masuk ke folder frontend
cd frontend

# 2. Jalankan dev server
npm run dev
```

**Expected Output:**

```
  VITE v5.0.8  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 4. Testing Upload

1. Buka browser: `http://localhost:5173`
2. Drag & drop video atau klik untuk upload
3. Tunggu upload selesai
4. Pastikan muncul info video (ukuran, durasi, status)

**Troubleshooting Upload:**

- ❌ "File too large" → Gunakan video < 2GB
- ❌ "Video too long" → Gunakan video < 60 menit
- ❌ "Invalid file type" → Gunakan MP4, MOV, atau AVI

### 5. Testing Processing

1. Pilih pengaturan:

   - Bahasa: Indonesia/English
   - Durasi: Pilih "Semua" untuk testing
   - Gaya: Pilih "Seimbang"

2. Klik "Generate Klip Sekarang"

3. Monitor progress:
   - Analisis Video (0-40%)
   - Analisis Audio (40-70%)
   - Generate Klip (70-100%)

**Expected Timeline:**

- Video 5 menit: ~2-3 menit processing
- Video 10 menit: ~4-6 menit processing
- Video 15 menit: ~6-10 menit processing

**Troubleshooting Processing:**

- ❌ "FFmpeg not found" → Install FFmpeg dan tambahkan ke PATH
- ❌ "Whisper model download failed" → Check koneksi internet
- ❌ "Memory error" → Gunakan video lebih pendek atau model Whisper lebih kecil

### 6. Testing Results

Setelah processing selesai, check:

✅ **Jumlah Klip**: Minimal 3-5 klip untuk video 10 menit
✅ **Skor Viral**: Minimal ada 1 klip dengan skor "Tinggi"
✅ **Kategori**: Klip ter-kategorisasi dengan benar
✅ **Preview**: Video bisa di-preview dengan hover
✅ **Download**: Klip bisa di-download individual
✅ **Download All**: Semua klip bisa di-download sebagai ZIP

### 7. Manual Testing Checklist

#### Upload Flow

- [ ] Drag & drop works
- [ ] File picker works
- [ ] File validation works (size, duration, format)
- [ ] Upload progress shows
- [ ] Error messages clear

#### Settings Flow

- [ ] Language selection works
- [ ] Duration selection works
- [ ] Style selection works
- [ ] Settings saved correctly

#### Processing Flow

- [ ] Processing starts correctly
- [ ] Progress bar updates
- [ ] Status messages update
- [ ] Processing completes without errors
- [ ] Error handling works

#### Results Flow

- [ ] Clips display correctly
- [ ] Preview on hover works
- [ ] Modal opens on click
- [ ] Video playback works
- [ ] Download single clip works
- [ ] Download all clips works
- [ ] Metadata accurate (duration, timestamp, category)

### 8. Performance Testing

**Test dengan berbagai ukuran video:**

| Video Duration | Expected Processing Time | Expected Clips |
| -------------- | ------------------------ | -------------- |
| 5 minutes      | 2-3 minutes              | 3-5 clips      |
| 10 minutes     | 4-6 minutes              | 5-8 clips      |
| 15 minutes     | 6-10 minutes             | 7-10 clips     |
| 30 minutes     | 12-20 minutes            | 10 clips (max) |

### 9. Quality Testing

**Check kualitas klip yang dihasilkan:**

✅ **Hook Quality**: Apakah klip dimulai dengan hook yang kuat?
✅ **Content Value**: Apakah isi klip informatif/menarik?
✅ **Ending Impact**: Apakah ending klip "nendang"?
✅ **Audio Quality**: Apakah audio jelas tanpa jeda panjang?
✅ **Visual Quality**: Apakah ada wajah/aktivitas visual?

### 10. Edge Cases

Test dengan kondisi ekstrim:

- [ ] Video tanpa audio → Should fail gracefully
- [ ] Video tanpa dialog (hanya musik) → Should generate clips based on visual
- [ ] Video dengan banyak jeda → Should skip silent parts
- [ ] Video dengan banyak filler words → Should filter them out
- [ ] Video dengan multiple speakers → Should handle correctly

### 11. Browser Compatibility

Test di berbagai browser:

- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (Mac)

### 12. Sample Test Videos

**Buat atau download video test dengan karakteristik:**

1. **Educational Video** (5 min)

   - Tutorial/how-to content
   - Expected: High educational score

2. **Entertainment Video** (5 min)

   - Comedy/funny content
   - Expected: High entertaining score

3. **Opinion/Rant Video** (5 min)

   - Strong opinions, controversial
   - Expected: High controversial score

4. **Story/Vlog Video** (5 min)
   - Personal story, emotional
   - Expected: High emotional score

### 13. Debugging

Jika ada masalah, check:

```bash
# Backend logs
cd backend
python app.py  # Check terminal output

# Frontend logs
# Open browser console (F12)
# Check for errors

# Check uploaded files
ls backend/uploads/

# Check generated clips
ls backend/outputs/
```

### 14. Clean Up After Testing

```bash
# Delete test uploads
rm -rf backend/uploads/*
rm -rf backend/outputs/*

# Keep .gitkeep files
touch backend/uploads/.gitkeep
touch backend/outputs/.gitkeep
```

## Expected Results

Setelah testing berhasil, kamu harus bisa:

1. ✅ Upload video tanpa error
2. ✅ Process video dan dapat 5-10 klip
3. ✅ Preview klip dengan smooth
4. ✅ Download klip individual dan ZIP
5. ✅ Klip punya skor viral yang masuk akal
6. ✅ Transkrip akurat (minimal 80-90%)
7. ✅ Kategori klip sesuai konten

## Troubleshooting Common Issues

### Issue: "Module not found"

```bash
# Re-install dependencies
cd backend
pip install -r requirements.txt

cd ../frontend
npm install
```

### Issue: "FFmpeg not found"

```bash
# Windows: Download from https://ffmpeg.org/
# Add to PATH or copy ffmpeg.exe to backend/

# Linux:
sudo apt install ffmpeg

# Mac:
brew install ffmpeg
```

### Issue: "Whisper model slow"

```python
# Edit backend/config.py
WHISPER_MODEL = 'tiny'  # Faster but less accurate
# or
WHISPER_MODEL = 'base'  # Balanced (recommended)
```

### Issue: "Out of memory"

- Use smaller Whisper model
- Process shorter videos
- Close other applications

---

**Happy Testing! 🚀**
