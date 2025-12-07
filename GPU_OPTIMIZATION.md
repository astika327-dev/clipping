# GPU Optimization Guide - RTX 3060

## Overview
Backend dioptimalkan untuk memanfaatkan NVIDIA RTX 3060 secara maksimal:
- **GPU untuk Whisper** (transkripsi audio) - float16 precision
- **GPU untuk FFmpeg** (export video) - CUDA decoder + NVENC encoder + GPU filters
- **Batch processing** untuk multiple clips

## Hardware Specs (RTX 3060)
- VRAM: 12GB (9.7GB tersedia untuk aplikasi)
- CUDA Compute: 12.8 (cuBLAS)
- TFLOPS: 12.4
- Memory Bandwidth: 317.2 GB/s

## Configuration Settings

### 1. Whisper (Audio Transcription)
**File:** `backend/config.py`

```python
FASTER_WHISPER_DEVICE = 'cuda'
FASTER_WHISPER_COMPUTE_TYPE = 'float16'
```

**Penjelasan:**
- `cuda`: Menggunakan GPU NVIDIA untuk transcription
- `float16`: Precision level yang optimal untuk RTX 3060 (lebih cepat, VRAM lebih efisien)
- Alternatif: `int8_float16` jika ingin mixed precision

**Kecepatan:**
- GPU (CUDA): ~5-10 menit untuk 1 jam video
- CPU: ~30-60 menit untuk 1 jam video

### 2. FFmpeg Video Export
**File:** `backend/config.py`

```python
# Codec
VIDEO_CODEC = 'h264_nvenc'  # atau 'hevc_nvenc' untuk H.265
# VIDEO_CODEC = 'hevc_nvenc'  # Uncomment untuk H.265 (better compression)

# GPU Settings
USE_GPU_ACCELERATION = True
HWACCEL_DECODER = 'cuda'
HWACCEL_OUTPUT_FORMAT = 'cuda'
USE_GPU_FILTERS = True
SCALE_FILTER = 'scale_cuda'

# Quality
NVENC_PRESET = 'medium'  # slow, medium, fast
NVENC_RC_MODE = 'vbr'  # vbr, cbr, cqp
NVENC_QUALITY = 25  # 0=best, 51=worst

# Performance
VIDEO_BITRATE = '4M'
AUDIO_BITRATE = '192k'
MAX_PARALLEL_EXPORTS = 2
```

**Penjelasan Component:**

| Setting | Value | Penjelasan |
|---------|-------|-----------|
| `h264_nvenc` | Codec | NVIDIA GPU encoder untuk H.264 (kompatibel luas) |
| `hevc_nvenc` | Codec Alternative | NVIDIA GPU encoder untuk H.265 (40% lebih kecil, same quality) |
| `HWACCEL_DECODER: cuda` | Decoding | Gunakan GPU untuk decode input video |
| `HWACCEL_OUTPUT_FORMAT: cuda` | Memory | Simpan frame di GPU (avoid CPU-GPU transfer) |
| `scale_cuda` | GPU Filter | Gunakan GPU scaling (lebih cepat) |
| `medium` | NVENC Preset | Balanced quality vs speed (slow=best, fast=speed) |
| `vbr` | Rate Control | Variable bitrate (adaptive quality) |
| `4M` | Bitrate | RTX 3060 bisa handle 4Mbps smooth |

## Performance Comparison

### Example: 10-minute video → 3 clips export

| Method | Time | Quality | File Size |
|--------|------|---------|-----------|
| **GPU (NVENC)** | ~30 sec | Good | 12-15 MB |
| **CPU (libx264)** | ~3-5 min | Same | 12-15 MB |
| **GPU (HEVC)** | ~40 sec | Same | 8-10 MB |

**Speedup:** GPU adalah **6-10x lebih cepat** untuk export!

## Advanced Tuning for RTX 3060

### If You Want Faster Export (Quality ↓)
```python
NVENC_PRESET = 'fast'
VIDEO_BITRATE = '2.5M'
```

### If You Want Better Quality (Speed ↓)
```python
NVENC_PRESET = 'slow'  # Warning: ~2x slower
VIDEO_BITRATE = '6M'
```

### If You Want Smaller Files (HEVC)
```python
VIDEO_CODEC = 'hevc_nvenc'  # H.265
# File size ~40% lebih kecil, tapi kompatibilitas lebih terbatas
```

### For Multiple Parallel Exports
```python
MAX_PARALLEL_EXPORTS = 2  # RTX 3060 VRAM: 12GB
# Dengan 3 clips @ ~3-4MB masing-masing + Whisper = safe di 2 parallel
```

## Monitor GPU Usage

### Check Real-Time GPU Stats
```bash
# Terminal baru di server
nvidia-smi  # Lihat live GPU usage
nvidia-smi -l 1  # Auto-refresh setiap 1 detik

# During export process, expect:
# - Decode: ~30-40% GPU util
# - Filter: ~20-30% GPU util
# - Encode: ~60-80% GPU util
```

### Check GPU Memory
```bash
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
# Expected: ~4-6GB used (out of 12GB)
```

## Troubleshooting

### Error: "hwaccel cuda not available"
**Solusi:** Pastikan FFmpeg diinstall dengan CUDA support
```bash
ffmpeg -hwaccels  # Should show "cuda"
```

### Error: "scale_cuda filter not found"
**Solusi:** Set `USE_GPU_FILTERS = False` di config.py, gunakan CPU filter
```python
USE_GPU_FILTERS = False  # Fallback ke CPU scale
```

### Export tetap lambat (CPU fallback)
**Diagnosa:**
1. Cek log backend: apakah ada error pada GPU?
2. Cek `nvidia-smi`: apakah GPU terdeteksi?
3. Cek FFmpeg: `ffmpeg -codecs | grep nvenc`

### VRAM penuh
**Solusi:**
1. Kurangi `MAX_PARALLEL_EXPORTS = 1`
2. Kurangi `VIDEO_BITRATE`
3. Restart backend untuk clear GPU memory

## Environment Variables (Optional Override)

```bash
# Uncomment di server untuk override config
export FASTER_WHISPER_DEVICE=cuda
export FASTER_WHISPER_COMPUTE_TYPE=float16
export VIDEO_CODEC=h264_nvenc
export NVENC_PRESET=medium
export MAX_PARALLEL_EXPORTS=2
```

## Recommended Setup for RTX 3060

```python
# For Balanced Performance (Recommended)
FASTER_WHISPER_DEVICE = 'cuda'
FASTER_WHISPER_COMPUTE_TYPE = 'float16'
VIDEO_CODEC = 'h264_nvenc'
NVENC_PRESET = 'medium'
VIDEO_BITRATE = '4M'
AUDIO_BITRATE = '192k'
MAX_PARALLEL_EXPORTS = 2
USE_GPU_FILTERS = True

# For Speed (Sacrifice Quality)
# VIDEO_CODEC = 'hevc_nvenc'
# NVENC_PRESET = 'fast'
# VIDEO_BITRATE = '2.5M'

# For Quality (Slower)
# NVENC_PRESET = 'slow'
# VIDEO_BITRATE = '6M'
```

## Next Steps

1. **Verify GPU is working:**
   ```bash
   ssh -p 55157 root@185.62.108.226
   cd /workspace/clipping/backend
   python app.py --production --port 5000
   # Upload video → watch GPU spike in nvidia-smi
   ```

2. **Monitor during export:**
   ```bash
   # Terminal baru:
   ssh -p 55157 root@185.62.108.226
   watch -n 0.1 nvidia-smi
   ```

3. **Check logs:**
   ```
   Backend logs akan menampilkan:
   "🎬 GPU Acceleration: True | GPU Filters: True | Codec: h264_nvenc"
   "✅ Clip exported successfully"
   ```

## References

- [FFmpeg NVIDIA Encoding (NVENC)](https://developer.nvidia.com/nvidia-video-codec-sdk)
- [FFmpeg CUDA Acceleration](https://trac.ffmpeg.org/wiki/HWAccelIntro#NVIDIA)
- [Faster Whisper GPU Docs](https://github.com/SYSTRAN/faster-whisper#gpu)
- [NVIDIA NVENC Developer Documentation](https://docs.nvidia.com/video-technologies/video-codec-sdk/12.0/ffmpeg-with-nvidia-gpu/)

---

**Last Updated:** December 7, 2025  
**GPU:** RTX 3060 (12GB VRAM)  
**Optimizations:** CUDA decoder + NVENC encoder + GPU filters
