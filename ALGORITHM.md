# 🧠 Algoritma Pemilihan Klip - AI Video Clipper

## Overview

Aplikasi ini menggunakan kombinasi analisis audio (speech-to-text) dan analisis visual (computer vision) untuk mengidentifikasi dan memilih segmen video yang paling menarik untuk dijadikan klip pendek.

## Pipeline Lengkap

```
Video Input
    ↓
┌─────────────────────────────────────┐
│  1. VIDEO ANALYSIS                  │
│  - Scene Detection                  │
│  - Face Detection                   │
│  - Motion Analysis                  │
│  - Brightness Analysis              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. AUDIO ANALYSIS                  │
│  - Speech-to-Text (Whisper)         │
│  - Keyword Detection                │
│  - Hook Identification              │
│  - Punchline Detection              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. SEGMENT MERGING                 │
│  - Combine Video + Audio Analysis   │
│  - Align Timestamps                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. SCORING & RANKING               │
│  - Calculate Viral Score            │
│  - Rank Segments                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  5. CLIP SELECTION                  │
│  - Select Top Segments              │
│  - Adjust Durations                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  6. EXPORT                          │
│  - Cut Video (FFmpeg)               │
│  - Generate Metadata                │
└─────────────────────────────────────┘
    ↓
Clips Output
```

---

## 1. Video Analysis

### 1.1 Scene Detection

**Library**: `scenedetect` dengan `ContentDetector`

**Cara Kerja**:

- Menganalisis perubahan konten antar frame
- Threshold: 27.0 (dapat disesuaikan di config)
- Menghasilkan list scene dengan timestamp start/end

**Output**:

```python
scenes = [
    (start_time: 0.0, end_time: 15.3),
    (start_time: 15.3, end_time: 32.1),
    ...
]
```

**Filtering**:

- Scene < 3 detik diabaikan (terlalu pendek)
- Scene > 60 detik di-split (terlalu panjang)

### 1.2 Face Detection

**Library**: OpenCV Haar Cascade

**Cara Kerja**:

- Sample 5 frame per scene
- Detect faces di setiap frame
- Hitung rata-rata jumlah wajah

**Scoring**:

```python
face_score = min(avg_faces / 2.0, 1.0)
# 2+ wajah = skor maksimal
# 1 wajah = skor 0.5
# 0 wajah = skor 0
```

**Interpretasi**:

- `has_faces = True` → Ada wajah terdeteksi
- `has_closeup = True` → Rata-rata > 0.5 wajah (likely close-up)

### 1.3 Motion Analysis

**Cara Kerja**:

- Hitung perbedaan antar frame (frame differencing)
- `motion_score = mean(abs_diff(frame_t, frame_t-1))`

**Scoring**:

```python
motion_score = min(avg_motion / 50.0, 1.0)
# Motion > 50 = skor maksimal
# Motion < 10 = skor rendah (static)
```

**Interpretasi**:

- High motion → Aktivitas tinggi, engaging
- Low motion → Static, mungkin boring

### 1.4 Visual Engagement Score

**Formula**:

```python
visual_engagement = (
    face_score * 0.5 +      # 50% - Wajah paling penting
    motion_score * 0.3 +    # 30% - Motion menambah interest
    brightness_score * 0.2  # 20% - Lighting yang baik
)
```

**Brightness Score**:

```python
brightness_score = 1.0 - abs(brightness - 127) / 127
# Optimal brightness = 127 (mid-gray)
# Too dark/bright = skor rendah
```

---

## 2. Audio Analysis

### 2.1 Speech-to-Text

**Model**: OpenAI Whisper

**Model Options**:

- `tiny`: Fastest, least accurate (~32x realtime)
- `base`: Fast, good accuracy (~16x realtime) **[RECOMMENDED]**
- `small`: Slower, better accuracy (~6x realtime)
- `medium`: Slow, very good accuracy (~2x realtime)
- `large`: Slowest, best accuracy (~1x realtime)

**Output**:

```python
{
    'language': 'id',
    'text': 'Full transcript...',
    'segments': [
        {
            'id': 0,
            'start': 0.0,
            'end': 5.2,
            'text': 'Halo semuanya...',
            'words': ['halo', 'semuanya']
        },
        ...
    ]
}
```

### 2.2 Keyword Detection

**Viral Keywords** (dari `config.py`):

1. **Hook Keywords**:

   - rahasia, secret, truth, fakta
   - shocking, mengejutkan, ternyata
   - jangan, never, harus, wajib

2. **Emotional Keywords**:

   - gagal, sukses, menang, kalah
   - sedih, bahagia, marah, bangga

3. **Controversial Keywords**:

   - kontroversial, debat, salah, benar
   - bohong, jujur, truth

4. **Educational Keywords**:

   - cara, how to, tips, tutorial
   - belajar, learn, panduan

5. **Entertaining Keywords**:
   - lucu, funny, ngakak, kocak
   - gila, crazy, epic, amazing

**Scoring**:

```python
keyword_score = min(matches / 3.0, 1.0)
# 3+ matches = skor maksimal
# 1 match = skor 0.33
# 0 match = skor 0
```

### 2.3 Hook Detection

**Definisi Hook**: Kalimat pembuka yang kuat, biasanya di awal video atau setelah scene change.

**Cara Deteksi**:

1. Analisis 5 segment pertama
2. Check untuk hook keywords
3. Prioritaskan segment dengan:
   - Hook keywords > 0.3
   - Di awal video (0-30 detik)
   - Kalimat pendek & padat

**Contoh Hook Kuat**:

- ❌ "Jadi gini ya guys, ehm, anu..."
- ✅ "Ini rahasia yang gak pernah diomongin!"
- ✅ "3 kesalahan fatal yang harus kamu hindari"

### 2.4 Punchline Detection

**Definisi Punchline**: Statement yang impactful, biasanya di akhir segment.

**Cara Deteksi**:

1. Check emotional + controversial keywords
2. Check untuk exclamation marks (!)
3. Prioritaskan segment dengan:
   - Emotional score > 0.4
   - Controversial score > 0.4
   - Ada tanda seru

**Contoh Punchline**:

- ✅ "Dan ternyata, semuanya bohong!"
- ✅ "Inilah yang bikin saya bangkrut"
- ✅ "Jangan pernah percaya sama mereka!"

### 2.5 Content Engagement Score

**Formula**:

```python
engagement = (
    hook_score * 0.25 +           # 25% - Hook strength
    emotional_score * 0.20 +      # 20% - Emotional impact
    controversial_score * 0.15 +  # 15% - Controversial/opini
    educational_score * 0.15 +    # 15% - Educational value
    entertaining_score * 0.15 +   # 15% - Entertainment value
    question_bonus +              # +0.2 if has question
    numbers_bonus -               # +0.15 if has numbers/stats
    filler_penalty                # -0.1 per filler word (max -0.5)
)
```

**Filler Words** (dikurangi skornya):

- Indonesian: ehm, anu, jadi, gitu, kayak, terus, nah
- English: umm, uh, like, you know, i mean, basically

---

## 3. Segment Merging

**Tujuan**: Menggabungkan analisis video (scenes) dengan analisis audio (segments).

**Cara Kerja**:

1. Untuk setiap scene dari video analysis
2. Cari audio segments yang overlap dengan scene
3. Gabungkan text dari semua overlapping segments
4. Rata-rata audio scores
5. Combine dengan visual scores

**Output**:

```python
merged_segment = {
    'start': 15.3,
    'end': 32.1,
    'duration': 16.8,
    'text': 'Combined transcript...',
    'visual': {
        'has_faces': True,
        'visual_engagement': 0.75
    },
    'audio': {
        'hook': 0.6,
        'emotional': 0.4,
        'engagement': 0.7
    }
}
```

---

## 4. Viral Score Calculation

**Formula Lengkap**:

```python
viral_score = (
    hook_strength * 0.30 +        # 30% - Hook di awal
    content_value * 0.25 +        # 25% - Nilai konten
    visual_engagement * 0.20 +    # 20% - Visual appeal
    audio_engagement * 0.15 +     # 15% - Audio quality
    pacing * 0.10 +               # 10% - Pacing (tidak terlalu panjang)
    style_bonus                   # Bonus berdasarkan style
)
```

### 4.1 Hook Strength (30%)

```python
hook_strength = audio['hook'] * 0.30
```

**Pentingnya**: Hook adalah elemen PALING PENTING untuk TikTok. 3 detik pertama menentukan apakah viewer akan skip atau lanjut nonton.

### 4.2 Content Value (25%)

```python
content_value = (
    audio['emotional'] * 0.10 +
    audio['educational'] * 0.08 +
    audio['entertaining'] * 0.07
)
```

**Pentingnya**: Konten harus punya value - entah menghibur, mendidik, atau menyentuh emosi.

### 4.3 Visual Engagement (20%)

```python
visual_engagement = visual['visual_engagement'] * 0.20

# Bonus:
if visual['has_closeup']:
    visual_engagement += 0.05
if visual['has_high_motion']:
    visual_engagement += 0.05
```

**Pentingnya**: Visual yang menarik (wajah, gerakan) membuat viewer tetap engaged.

### 4.4 Audio Engagement (15%)

```python
audio_engagement = audio['engagement'] * 0.15
```

**Pentingnya**: Audio yang jelas, tanpa jeda panjang, tanpa filler words.

### 4.5 Pacing (10%)

```python
pacing = 0.10 if duration < 30 else 0.05
```

**Pentingnya**: Klip pendek lebih engaging. TikTok audience punya attention span pendek.

### 4.6 Style Bonus

```python
if style == 'funny':
    style_bonus = audio['entertaining'] * 0.10
elif style == 'educational':
    style_bonus = audio['educational'] * 0.10
elif style == 'dramatic':
    style_bonus = audio['emotional'] * 0.10
elif style == 'controversial':
    style_bonus = audio['controversial'] * 0.10
else:  # balanced
    style_bonus = 0
```

**Pentingnya**: User bisa pilih style yang mereka mau, dan algoritma akan prioritaskan klip yang sesuai.

---

## 5. Clip Selection

### 5.1 Filtering by Duration

**Target Durations**:

- Short: 9-15 detik
- Medium: 18-22 detik
- Long: 28-32 detik

**Cara Kerja**:

1. Filter segments berdasarkan target duration
2. Jika tidak ada yang pas, adjust duration:
   - Terlalu panjang → Trim dari akhir
   - Terlalu pendek (tapi > 70% target) → Extend sedikit

### 5.2 Ranking & Selection

```python
# Sort by viral score
segments.sort(key=lambda x: x['viral_score'], reverse=True)

# Select top N
selected = segments[:MAX_CLIPS_PER_VIDEO]

# Filter by minimum score
selected = [s for s in selected if s['viral_score'] >= MIN_VIRAL_SCORE]
```

**Default Settings**:

- `MAX_CLIPS_PER_VIDEO = 10`
- `MIN_VIRAL_SCORE = 0.5`

### 5.3 Clip Quality Checks

Setiap klip harus memenuhi:

✅ **Hook Check**:

- Apakah 3 detik pertama punya hook?
- Jika tidak, coba adjust start time

✅ **Content Check**:

- Apakah ada konten yang jelas?
- Tidak hanya jeda atau filler words

✅ **Ending Check**:

- Apakah ending "nendang"?
- Ada punchline atau cliffhanger?

---

## 6. Category Assignment

**Cara Menentukan Kategori**:

```python
categories = {
    'educational': audio['educational'],
    'entertaining': audio['entertaining'],
    'emotional': audio['emotional'],
    'controversial': audio['controversial']
}

category = max(categories, key=categories.get)
```

**Emoji per Kategori**:

- 📚 Educational
- 😂 Entertaining
- ❤️ Emotional
- 🔥 Controversial

---

## 7. Viral Level Assignment

**Konversi Score ke Level**:

```python
if viral_score >= 0.75:
    level = 'Tinggi'      # High potential
elif viral_score >= 0.5:
    level = 'Sedang'      # Medium potential
else:
    level = 'Rendah'      # Low potential
```

**Interpretasi**:

- **Tinggi (0.75-1.0)**: Klip ini punya semua elemen viral - hook kuat, konten menarik, visual engaging
- **Sedang (0.5-0.75)**: Klip bagus tapi mungkin kurang 1-2 elemen
- **Rendah (< 0.5)**: Klip ini di-filter out (tidak dihasilkan)

---

## 8. Reason Generation

**Cara Generate Alasan**:

```python
reasons = []

if audio['hook'] > 0.5:
    reasons.append('hook kuat')
if audio['emotional'] > 0.5:
    reasons.append('konten emosional')
if audio['controversial'] > 0.5:
    reasons.append('opini kontroversial')
if visual['has_closeup']:
    reasons.append('close-up speaker')
if visual['has_high_motion']:
    reasons.append('visual dinamis')

reason = ' + '.join(reasons).capitalize()
```

**Contoh Output**:

- "Hook kuat + konten emosional + close-up speaker"
- "Opini kontroversial + visual dinamis"
- "Konten informatif + hook kuat"

---

## 9. Optimizations & Future Improvements

### Current Limitations

1. **Face Detection**: Basic Haar Cascade (bisa upgrade ke deep learning model)
2. **Emotion Detection**: Keyword-based (bisa upgrade ke sentiment analysis)
3. **Scene Detection**: Content-based only (bisa tambah audio-based)
4. **Filler Word Removal**: Detection only (belum auto-remove dari audio)

### Planned Improvements v2.0

1. **Advanced Emotion Detection**:

   - Use sentiment analysis model
   - Detect tone of voice (angry, happy, sad)

2. **Better Face Detection**:

   - Use MTCNN or RetinaFace
   - Detect facial expressions

3. **Auto Subtitle Generation**:

   - Generate SRT from Whisper
   - Burn subtitles into video

4. **Smart Trimming**:

   - Auto-remove filler words from audio
   - Smooth transitions

5. **Music Detection**:

   - Detect background music
   - Suggest trending music

6. **Batch Processing**:
   - Process multiple videos at once
   - Queue system

---

## 10. Performance Considerations

### Time Complexity

- **Video Analysis**: O(n) where n = number of frames
- **Audio Analysis**: O(m) where m = audio duration
- **Scoring**: O(k) where k = number of segments
- **Total**: O(n + m + k) ≈ Linear with video duration

### Space Complexity

- **Video in memory**: Not loaded entirely (streaming)
- **Whisper model**: ~140MB (base model)
- **Temporary files**: ~2x video size

### Bottlenecks

1. **Whisper Transcription**: Slowest part (60-70% of total time)
2. **Scene Detection**: Medium (20-30% of total time)
3. **Face Detection**: Fast (5-10% of total time)

### Optimization Tips

1. Use smaller Whisper model for faster processing
2. Reduce scene detection threshold for fewer scenes
3. Sample fewer frames for face detection
4. Use GPU for Whisper (if available)

---

**Dokumentasi ini menjelaskan seluruh algoritma yang digunakan dalam AI Video Clipper. Untuk pertanyaan lebih lanjut, silakan buka issue di GitHub atau hubungi developer.**
