# Peningkatan Fitur Viral & Format 16:9

## 🎯 Ringkasan Perubahan

Sistem video clipper telah ditingkatkan dengan fitur-fitur berikut untuk menghasilkan konten yang lebih viral:

### 1. **Algoritma Viral Scoring yang Ditingkatkan** ✨

#### Bobot Baru (Lebih Agresif):
- **Hook Strength**: 30% → **35%** (meningkat 5%)
- **Audio Engagement**: 15% → **25%** (meningkat 10%)
- **Visual Engagement**: 20% → **25%** (meningkat 5%)
- **Pacing Score**: 
  - Clip ≤15s: **15%** (sangat pendek = viral)
  - Clip ≤25s: **10%**
  - Clip >25s: **5%**

#### Bonus Visual Tambahan:
- Face closeup: **+8%** (dari 5%)
- High motion: **+8%** (dari 5%)
- Face detection: **+5%** (baru)

#### Bonus Konten:
- Mengandung pertanyaan (?): **+5%**
- Mengandung angka/statistik: **+5%**
- Mengandung tanda seru (!): **+5%**

### 2. **Keyword Viral Indonesia yang Diperluas** 🇮🇩

#### Kategori Baru:
- **Money Keywords** (15% weight): cuan, omset, closing, deal, profit, gaji, bonus, komisi, dll
- **Urgency Keywords** (15% weight): sekarang, segera, cepat, deadline, terbatas, hari ini, dll

#### Keyword yang Ditambahkan:

**Hook Keywords** (+15):
- dengerin, perhatikan, bongkar, bocor, exposed
- terbukti, brutal, savage, mentah, blak-blakan
- catet, ingat, stop, quit, selesai

**Emotional Keywords** (+10):
- hancur, ambyar, meledak, boom
- gelisah, takut, berani
- nyerah, lawan, perjuangan

**Controversial Keywords** (+6):
- problematik, toxic, racun
- penipu, scam, tipu-tipu
- konspirasi, manipulasi

**Educational Keywords** (+7):
- strategi, teknik, metode, sistem
- formula, blueprint, framework

**Entertaining Keywords** (+5):
- absurd, aneh, unik
- tak terduga, plot twist
- spektakuler

### 3. **Format Video 16:9 Otomatis** 📺

Setiap clip yang diekspor akan otomatis:
- **Resolusi**: 1920x1080 (Full HD 16:9)
- **Scaling**: Proporsional dengan padding hitam
- **Codec**: H.264 (libx264) untuk kompatibilitas maksimal
- **Bitrate**: 2M video, 128k audio

**Contoh FFmpeg Filter:**
```
scale=1920:1080:force_original_aspect_ratio=decrease,
pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black
```

### 4. **Hook Overlay Otomatis di Awal Video** 🎬

Fitur hook otomatis yang dapat diaktifkan dengan `use_timoty_hooks: true`:

#### Konfigurasi Default:
- **Durasi**: 4 detik
- **Font Size**: 48pt
- **Warna**: White text dengan background hitam semi-transparan
- **Posisi**: Center (bisa diatur: top/center/bottom)
- **Animasi**: Fade in/out (0.5s each)

#### Cara Hook Dibuat:
Hook dihasilkan secara otomatis dari `TimotyHookGenerator` berdasarkan:
- Tema konten (closing, money, mindset, urgency)
- Power words dalam transkrip
- Confidence score berdasarkan engagement metrics

**Contoh Hook:**
```
"Bro, dengerin bentar! Gue bongkar kenapa prospek kabur. 
Catet sekarang juga."
```

### 5. **Peningkatan Audio Analyzer** 🎤

#### Perubahan Scoring:
```python
engagement = (
    hook_score * 0.25 +
    emotional_score * 0.18 +
    controversial_score * 0.12 +
    educational_score * 0.12 +
    entertaining_score * 0.12 +
    money_score * 0.15 +      # BARU
    urgency_score * 0.15 +    # BARU
    question_bonus +
    numbers_bonus +
    emphasis_bonus -
    filler_penalty
)
```

#### Penalty Dikurangi:
- Filler word penalty: 0.1 → **0.08** per kata
- Max penalty: 0.5 → **0.4**

### 6. **Pengaturan Konfigurasi (config.py)**

#### Aspect Ratio Settings:
```python
TARGET_ASPECT_RATIO = '16:9'
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
```

#### Hook Overlay Settings:
```python
HOOK_ENABLED = True          # Enable/disable hook
HOOK_DURATION = 4.0          # Durasi tampil (detik)
HOOK_FONT_SIZE = 48          # Ukuran font
HOOK_FONT_COLOR = 'white'    # Warna text
HOOK_BG_COLOR = 'black@0.7'  # Background semi-transparan
HOOK_POSITION = 'center'     # top/center/bottom
HOOK_ANIMATION = 'fade'      # fade/slide/none
```

## 🚀 Cara Menggunakan

### 1. Aktifkan Hook Timoty via API:
```json
POST /api/process
{
  "filename": "video.mp4",
  "language": "id",
  "target_duration": "short",
  "style": "balanced",
  "use_timoty_hooks": true
}
```

### 2. Aktifkan Caption Otomatis:
```json
{
  "auto_caption": true
}
```

### 3. Kustomisasi di config.py:
```python
# Nonaktifkan hook
HOOK_ENABLED = False

# Ubah durasi hook
HOOK_DURATION = 5.0

# Ubah posisi hook
HOOK_POSITION = 'top'

# Nonaktifkan animasi
HOOK_ANIMATION = 'none'
```

## 📊 Hasil yang Diharapkan

Dengan peningkatan ini, sistem akan:
1. ✅ Menghasilkan clip dengan format 16:9 (optimal untuk semua platform)
2. ✅ Mendeteksi konten viral lebih akurat (money, urgency keywords)
3. ✅ Memberikan skor lebih tinggi untuk clip pendek dan engaging
4. ✅ Menambahkan hook otomatis di awal setiap clip
5. ✅ Menghasilkan clip yang lebih "punchy" dan attention-grabbing

## 🎯 Metrik Viral Score

**Viral Score Tinggi (≥0.75):**
- Hook kuat (35%)
- Engagement tinggi (25%)
- Visual menarik (25%)
- Konten pendek (<15s)
- Mengandung money/urgency keywords

**Viral Score Sedang (0.5-0.75):**
- Hook moderate
- Visual atau audio engaging
- Durasi medium (15-25s)

**Viral Score Rendah (<0.5):**
- Hook lemah
- Konten informatif standar
- Durasi panjang (>25s)

## 🔧 Troubleshooting

### Hook tidak muncul:
- Pastikan `HOOK_ENABLED = True` di config.py
- Pastikan `use_timoty_hooks: true` di request
- Cek apakah font Arial.ttf ada di sistem

### Video tidak 16:9:
- Cek FFmpeg terinstall
- Cek log FFmpeg untuk error
- Pastikan resolusi input cukup

### Viral score terlalu rendah:
- Coba style berbeda (funny, controversial, dramatic)
- Pastikan video mengandung keyword viral
- Cek transkrip untuk akurasi

## 🎬 Auto-Cut Dead Air (NEW!)

### Fitur Otomatis Menghapus Jeda Panjang

Sistem sekarang dapat mendeteksi dan menghapus "dead air" (jeda/silence panjang) secara otomatis untuk membuat clip lebih dinamis dan engaging.

#### Cara Kerja:
1. **Deteksi Silence**: FFmpeg mendeteksi bagian audio yang di bawah threshold tertentu
2. **Penalty Scoring**: Segment dengan banyak silence mendapat penalty pada viral score
3. **Auto-Cut**: Saat export, FFmpeg otomatis membuang silence gap dengan `silenceremove` filter

#### Konfigurasi (config.py):
```python
ENABLE_DEAD_AIR_REMOVAL = True     # Enable/disable fitur
DEAD_AIR_THRESHOLD_DB = -35        # Suara di bawah ini = silence
MIN_DEAD_AIR_DURATION = 1.5        # Min. durasi silence untuk di-cut (detik)
KEEP_SILENCE_PADDING = 0.2         # Tetap simpan jeda ini (detik)
```

#### Efek:
- ✅ Clip lebih padat dan engaging
- ✅ Menghilangkan jeda awkward
- ✅ Meningkatkan retention rate
- ✅ Lebih cocok untuk konten viral short-form

#### Contoh:
**Before**: "Halo guys... [3 detik silence] ... jadi hari ini..."  
**After**: "Halo guys... [0.2 detik] jadi hari ini..."

#### Notes:
- Silence di awal dan akhir clip otomatis terpotong
- Silence di tengah dikurangi menjadi padding kecil (0.2s default)
- Tidak mempengaruhi kualitas audio/video
- Bisa dinonaktifkan dengan `ENABLE_DEAD_AIR_REMOVAL = False`

## 📝 Catatan

- Hook menggunakan font Arial (Windows default)
- Format 16:9 dengan padding hitam untuk video vertikal/horizontal
- Semua perubahan backward compatible
- Hook bisa dinonaktifkan tanpa mempengaruhi fungsionalitas lain
- Dead air removal menggunakan FFmpeg silenceremove filter

---

**Versi**: 2.1  
**Tanggal**: 5 Desember 2024  
**Status**: ✅ Production Ready
