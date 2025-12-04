# 📁 Struktur Project - AI Video Clipper

## Overview

```
c:\proyek\clipping\
├── backend/                    # Python Flask Backend
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration settings
│   ├── video_analyzer.py      # Video analysis module
│   ├── audio_analyzer.py      # Audio analysis module (Whisper)
│   ├── clip_generator.py      # Clip generation & export
│   ├── requirements.txt       # Python dependencies
│   ├── uploads/               # Uploaded videos (temporary)
│   └── outputs/               # Generated clips
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── main.jsx          # React entry point
│   │   ├── index.css         # Global styles (TailwindCSS)
│   │   └── components/
│   │       ├── VideoUploader.jsx      # Upload component
│   │       ├── SettingsPanel.jsx      # Settings component
│   │       ├── ProcessingStatus.jsx   # Processing UI
│   │       └── ClipResults.jsx        # Results display
│   ├── index.html            # HTML entry point
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite configuration
│   ├── tailwind.config.js    # TailwindCSS config
│   └── postcss.config.js     # PostCSS config
│
├── README.md                   # Main documentation
├── QUICKSTART.md              # Quick start guide
├── TESTING.md                 # Testing guide
├── ALGORITHM.md               # Algorithm documentation
└── .gitignore                 # Git ignore rules
```

## 📄 File Descriptions

### Backend Files

#### `app.py` (11.6 KB)

Main Flask application dengan endpoints:

- `POST /api/upload` - Upload video
- `POST /api/process` - Process video & generate clips
- `GET /api/status/<job_id>` - Get processing status
- `GET /api/download/<job_id>/<filename>` - Download single clip
- `GET /api/download-all/<job_id>` - Download all clips as ZIP
- `GET /api/preview/<job_id>/<filename>` - Preview clip
- `DELETE /api/cleanup/<job_id>` - Clean up job files

#### `config.py` (2.9 KB)

Configuration settings:

- Upload/output folders
- File size & duration limits
- Whisper model settings
- Clip duration targets
- Viral keywords
- Video export settings

#### `video_analyzer.py` (7.4 KB)

Video analysis module:

- Scene detection (scenedetect)
- Face detection (OpenCV Haar Cascade)
- Motion analysis (frame differencing)
- Brightness analysis
- Visual engagement scoring

#### `audio_analyzer.py` (9.6 KB)

Audio analysis module:

- Speech-to-text (Whisper)
- Keyword detection
- Hook identification
- Punchline detection
- Content engagement scoring

#### `clip_generator.py` (14.7 KB)

Clip generation module:

- Merge video + audio analysis
- Score segments
- Select best clips
- Generate metadata
- Export clips (FFmpeg)

#### `requirements.txt` (261 B)

Python dependencies:

- Flask & Flask-CORS
- OpenAI Whisper
- OpenCV
- scenedetect
- pydub
- torch & torchaudio
- ffmpeg-python

### Frontend Files

#### `src/App.jsx` (4.2 KB)

Main React component:

- State management
- Workflow orchestration
- Component composition

#### `src/components/VideoUploader.jsx` (4.5 KB)

Upload component:

- Drag & drop upload
- File validation
- Upload progress
- Error handling

#### `src/components/SettingsPanel.jsx` (3.8 KB)

Settings component:

- Language selection
- Duration target selection
- Style selection
- Process trigger

#### `src/components/ProcessingStatus.jsx` (3.2 KB)

Processing UI:

- Progress bar
- Status messages
- Step indicators
- Error display

#### `src/components/ClipResults.jsx` (6.9 KB)

Results component:

- Clips grid display
- Video preview
- Download functionality
- Clip details modal

#### `src/index.css` (2.5 KB)

Global styles:

- TailwindCSS imports
- Glassmorphism effects
- Custom animations
- Utility classes

#### `package.json` (597 B)

Node dependencies:

- React & ReactDOM
- Axios
- React Player
- Vite
- TailwindCSS

### Documentation Files

#### `README.md` (6.1 KB)

Main documentation:

- Project overview
- Features
- Tech stack
- Installation guide
- Usage instructions
- Configuration
- Troubleshooting
- Limitations

#### `QUICKSTART.md` (4.3 KB)

Quick start guide:

- Prerequisites
- Fast installation
- Basic usage
- Tips & tricks
- Quick troubleshooting

#### `TESTING.md` (7.0 KB)

Testing guide:

- Test preparation
- Testing checklist
- Performance testing
- Quality testing
- Edge cases
- Browser compatibility

#### `ALGORITHM.md` (15.4 KB)

Algorithm documentation:

- Complete pipeline
- Video analysis details
- Audio analysis details
- Scoring formulas
- Clip selection logic
- Performance considerations

## 🔄 Data Flow

```
1. USER uploads video
   ↓
2. Frontend sends to /api/upload
   ↓
3. Backend saves to uploads/
   ↓
4. Frontend sends to /api/process with settings
   ↓
5. Backend processes:
   a. VideoAnalyzer → scene detection, face detection
   b. AudioAnalyzer → transcription, keyword detection
   c. ClipGenerator → merge, score, select, export
   ↓
6. Backend saves clips to outputs/<job_id>/
   ↓
7. Frontend displays results
   ↓
8. USER previews & downloads clips
```

## 📊 File Sizes

**Total Project Size**: ~50 KB (code only, excluding dependencies)

**Backend**: ~46 KB

- Python code: ~44 KB
- Config: ~2 KB

**Frontend**: ~22 KB

- React components: ~18 KB
- Styles: ~2.5 KB
- Config: ~1.5 KB

**Documentation**: ~33 KB

- README: ~6 KB
- QUICKSTART: ~4 KB
- TESTING: ~7 KB
- ALGORITHM: ~15 KB

## 🎯 Key Features by File

### Video Analysis (`video_analyzer.py`)

- ✅ Scene detection with configurable threshold
- ✅ Face detection using Haar Cascade
- ✅ Motion analysis via frame differencing
- ✅ Visual engagement scoring

### Audio Analysis (`audio_analyzer.py`)

- ✅ Whisper transcription (multi-language)
- ✅ Hook detection (strong openings)
- ✅ Punchline detection (impactful statements)
- ✅ Keyword-based content categorization
- ✅ Filler word detection

### Clip Generation (`clip_generator.py`)

- ✅ Multi-factor viral scoring
- ✅ Style-based clip selection
- ✅ Duration-based filtering
- ✅ Automatic clip metadata generation
- ✅ FFmpeg-based video export

### Frontend UI (`src/components/`)

- ✅ Modern glassmorphism design
- ✅ Drag & drop upload
- ✅ Real-time progress tracking
- ✅ Video preview on hover
- ✅ Detailed clip information modal
- ✅ Batch download (ZIP)

## 🔧 Configuration Files

### Backend Config (`config.py`)

```python
MAX_VIDEO_SIZE = 2GB
MAX_VIDEO_DURATION = 60 minutes
WHISPER_MODEL = 'base'
CLIP_DURATIONS = [(9,15), (18,22), (28,32)]
MIN_VIRAL_SCORE = 0.5
MAX_CLIPS_PER_VIDEO = 10
```

### Frontend Config (`vite.config.js`)

```javascript
server.port = 5173
proxy: '/api' → 'http://localhost:5000'
```

### TailwindCSS Config (`tailwind.config.js`)

```javascript
Custom colors: primary, accent
Custom animations: pulse-slow, bounce-slow
```

## 📦 Dependencies

### Backend (Python)

- **Flask**: Web framework
- **Whisper**: Speech-to-text
- **OpenCV**: Computer vision
- **scenedetect**: Scene detection
- **FFmpeg**: Video processing

### Frontend (Node)

- **React**: UI framework
- **Vite**: Build tool
- **TailwindCSS**: Styling
- **Axios**: HTTP client

## 🚀 Deployment Considerations

### Production Checklist

- [ ] Set `WHISPER_MODEL` to 'small' or 'medium' for better accuracy
- [ ] Increase `MAX_VIDEO_SIZE` if needed
- [ ] Setup proper error logging
- [ ] Add rate limiting
- [ ] Setup HTTPS
- [ ] Add authentication (if needed)
- [ ] Setup background job queue (Celery)
- [ ] Add cloud storage (S3, GCS)

### Scaling Considerations

- Use Celery for async processing
- Use Redis for job queue
- Use cloud storage for videos
- Use CDN for clip delivery
- Add load balancer for multiple instances

---

**Last Updated**: 2025-12-03
**Version**: 1.0.0
