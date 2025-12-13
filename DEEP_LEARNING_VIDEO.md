# 🧠 Deep Learning Video Analysis

## Overview

Modul `advanced_video_analyzer.py` menyediakan analisis video berbasis deep learning yang jauh lebih akurat dibanding metode tradisional (Haar cascades).

## Fitur Utama

### 1. 🎭 MediaPipe Face Detection

- **468 facial landmarks** untuk deteksi wajah yang presisi
- Lebih akurat dibanding Haar cascade OpenCV
- Mendukung multiple faces dalam satu frame
- Real-time performance

### 2. 😊 Emotion/Expression Detection

Mendeteksi ekspresi berdasarkan facial landmarks:

- **Talking Detection**: Deteksi mulut terbuka → mengetahui kapan speaker berbicara
- **Smile Detection**: Analisis lebar mulut → mendeteksi kebahagiaan
- **Surprise Detection**: Analisis kelopak mata → mendeteksi keterkejutan
- **Engagement Score**: Kombinasi semua ekspresi

### 3. 🔍 YOLOv8 Object Detection

Mendeteksi objek relevan dalam frame:

- **Person count**: Berapa orang dalam frame (interview vs solo)
- **Tech objects**: Laptop, phone, keyboard, microphone
- **Scene context**: Membantu identify tipe konten

### 4. 🗣️ Speaker Activity Detection

Analisis aktivitas speaker tanpa full diarization:

- **Talking ratio**: Berapa persen waktu speaker berbicara
- **Speaker consistency**: Apakah wajah tetap di posisi sama
- **Engagement tracking**: Apakah speaker menunjukkan ekspresi

---

## Instalasi Dependencies

```bash
# Install deep learning dependencies
pip install mediapipe>=0.10.9
pip install ultralytics>=8.1.0
pip install fer>=22.5.1

# Atau install semua
pip install -r requirements.txt
```

---

## Konfigurasi

Set di `.env` atau environment variables:

```bash
# Enable/disable deep learning (default: true)
ENABLE_DEEP_LEARNING_VIDEO=true

# MediaPipe confidence threshold (0.0 - 1.0)
MEDIAPIPE_FACE_CONFIDENCE=0.5

# YOLO model size: n, s, m, l, x
# n = fastest (nano), x = most accurate (xlarge)
YOLO_MODEL_SIZE=n
YOLO_CONFIDENCE=0.5

# Speaker detection thresholds
SPEAKER_TALKING_THRESHOLD=0.3
SPEAKER_ENGAGEMENT_THRESHOLD=0.2
```

---

## Arsitektur

```
┌─────────────────────────────────────────────────────┐
│              AdvancedVideoAnalyzer                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────┐  ┌─────────────────┐          │
│  │ AdvancedFace    │  │ ObjectDetector  │          │
│  │ Analyzer        │  │ (YOLOv8)        │          │
│  │ (MediaPipe)     │  │                 │          │
│  └────────┬────────┘  └────────┬────────┘          │
│           │                    │                    │
│           ▼                    ▼                    │
│  ┌─────────────────┐  ┌─────────────────┐          │
│  │ Face Detection  │  │ Object Boxes    │          │
│  │ 468 Landmarks   │  │ Class Labels    │          │
│  │ Expression Scores│  │ Confidence      │          │
│  └────────┬────────┘  └────────┬────────┘          │
│           │                    │                    │
│           ▼                    ▼                    │
│  ┌─────────────────────────────────────────┐       │
│  │        SpeakerActivityDetector          │       │
│  │  - Talking ratio                        │       │
│  │  - Speaker consistency                  │       │
│  │  - Engagement tracking                  │       │
│  └────────────────────┬────────────────────┘       │
│                       │                             │
│                       ▼                             │
│  ┌─────────────────────────────────────────┐       │
│  │      Enhanced Visual Engagement Score    │       │
│  │  Base score + DL bonuses                 │       │
│  └─────────────────────────────────────────┘       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Output Fields

Setiap scene sekarang memiliki fields tambahan:

```python
scene = {
    # Standard fields
    'scene_id': 0,
    'start_time': 10.5,
    'end_time': 25.0,
    'duration': 14.5,

    # Deep Learning fields (NEW!)
    'is_talking': True,          # Apakah speaker sedang berbicara
    'is_engaged': True,          # Apakah ada ekspresi positif
    'expression': 'happy',       # Dominant expression
    'person_count': 1,           # Jumlah orang di frame
    'is_interview': False,       # True jika 2+ orang
    'talking_ratio': 0.75,       # 75% waktu berbicara
    'speaker_consistency': 0.9,  # Face position consistency

    # Enhanced engagement
    'visual_engagement': 0.85,   # DL-boosted score

    # Raw DL data
    'dl_face_analysis': {...},
    'dl_object_analysis': {...},
    'dl_speaker_analysis': {...}
}
```

---

## Performance

| Component           | GPU Time  | CPU Time   |
| ------------------- | --------- | ---------- |
| MediaPipe Face      | ~15ms     | ~50ms      |
| YOLOv8-n            | ~10ms     | ~80ms      |
| Speaker Analysis    | ~5ms      | ~20ms      |
| **Total per frame** | **~30ms** | **~150ms** |

Untuk video 30 FPS dengan 3 samples per scene:

- 50 scenes × 3 samples × 30ms = ~4.5 detik (GPU)
- 50 scenes × 3 samples × 150ms = ~22.5 detik (CPU)

---

## Fallback Behavior

Jika deep learning dependencies tidak terinstall:

1. MediaPipe fallback → Haar cascade OpenCV
2. YOLO fallback → Assume single person
3. Speaker detection fallback → Basic face tracking

Sistem tetap berjalan normal tanpa deep learning.

---

## Tips Optimasi

### Untuk Speed:

```bash
YOLO_MODEL_SIZE=n              # Gunakan nano model
MEDIAPIPE_FACE_CONFIDENCE=0.4  # Lower threshold
```

### Untuk Accuracy:

```bash
YOLO_MODEL_SIZE=m              # Gunakan medium model
MEDIAPIPE_FACE_CONFIDENCE=0.6  # Higher threshold
```

### Untuk Video Panjang (>1 jam):

Sistem otomatis mengurangi sampling untuk efisiensi.

---

## Troubleshooting

### Error: "MediaPipe not installed"

```bash
pip install mediapipe --upgrade
```

### Error: "YOLO model download failed"

Model akan di-download otomatis saat pertama kali. Pastikan koneksi internet.

### Slow performance on CPU

Set `ENABLE_DEEP_LEARNING_VIDEO=false` untuk disable deep learning jika tidak ada GPU.

---

_Documentation Version: 1.0_
_Last Updated: December 2024_
