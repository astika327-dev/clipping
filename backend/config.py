"""
Configuration file for AI Video Clipper
"""
import os
import shutil

class Config:
    # Auto-detect FFmpeg path from WinGet location if not in PATH
    if not shutil.which('ffmpeg'):
        print("⚠️ FFmpeg not found in PATH. Searching in common locations...")
        user_home = os.path.expanduser('~')
        
        # Specific path found on user's system
        specific_path = os.path.join(user_home, r'AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin')
        
        # Common WinGet path
        winget_path = os.path.join(user_home, r'AppData\Local\Microsoft\WinGet\Packages')
        
        found_ffmpeg = False
        
        if os.path.exists(specific_path) and os.path.exists(os.path.join(specific_path, 'ffmpeg.exe')):
            print(f"🔧 Found FFmpeg at: {specific_path}")
            os.environ['PATH'] += os.pathsep + specific_path
            found_ffmpeg = True
        elif os.path.exists(winget_path):
            for root, dirs, files in os.walk(winget_path):
                if 'ffmpeg.exe' in files:
                    ffmpeg_dir = root
                    print(f"🔧 Found FFmpeg at: {ffmpeg_dir}")
                    os.environ['PATH'] += os.pathsep + ffmpeg_dir
                    found_ffmpeg = True
                    break
        
        if not found_ffmpeg:
            print("❌ Could not find FFmpeg automatically. Please ensure it is installed and in PATH.")

    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'outputs')
    MAX_VIDEO_SIZE = 7 * 1024 * 1024 * 1024  # 7GB
    MAX_VIDEO_DURATION = 4 * 3600  # 4 hours - increased for long podcasts
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
    
    # YouTube download cookies configuration
    # Option 1: Export cookies to file using browser extension "Get cookies.txt LOCALLY"
    #           Then set: YTDLP_COOKIES_FILE=path/to/cookies.txt
    # Option 2: Use browser cookies directly (requires browser to be closed)
    #           Set: YTDLP_COOKIES_FROM_BROWSER=chrome (or firefox, edge, opera, brave)
    # Default: uses youtube_cookies.txt in backend folder if exists
    _default_cookie_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
    _env_cookie_file = os.environ.get('YTDLP_COOKIES_FILE', '').strip()
    YTDLP_COOKIES_FILE = os.path.expanduser(_env_cookie_file) if _env_cookie_file else (_default_cookie_file if os.path.exists(_default_cookie_file) else '')
    YTDLP_COOKIES_FROM_BROWSER = os.environ.get('YTDLP_COOKIES_FROM_BROWSER', '').strip()
    
    # Transcription settings - OPTIMIZED FOR SPEED
    TRANSCRIPTION_BACKEND = os.environ.get('TRANSCRIPTION_BACKEND', 'faster-whisper')
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'large')  # tiny, base, small, medium, large, large-v3
    WHISPER_FALLBACK_MODEL = os.environ.get('WHISPER_FALLBACK_MODEL', 'base')
    WHISPER_LANGUAGE = os.environ.get('WHISPER_LANGUAGE', 'id')  # Default: Indonesian
    FASTER_WHISPER_MODEL = os.environ.get('FASTER_WHISPER_MODEL', 'large')
    FASTER_WHISPER_FALLBACK_MODEL = os.environ.get('FASTER_WHISPER_FALLBACK_MODEL', 'base')
    FASTER_WHISPER_DEVICE = os.environ.get('FASTER_WHISPER_DEVICE', 'cpu')  # Use CPU for stability (set 'cuda' if GPU works)
    FASTER_WHISPER_COMPUTE_TYPE = os.environ.get('FASTER_WHISPER_COMPUTE_TYPE', 'int8')  # 'int8' for CPU, 'float16' for GPU
    FASTER_WHISPER_BEAM_SIZE = int(os.environ.get('FASTER_WHISPER_BEAM_SIZE', 1))  # Lower = faster
    FASTER_WHISPER_CHUNK_LENGTH = int(os.environ.get('FASTER_WHISPER_CHUNK_LENGTH', 30))
    FASTER_WHISPER_VAD_FILTER = os.environ.get('FASTER_WHISPER_VAD_FILTER', 'true').lower() == 'true'  # Skip silent parts (30-50% faster)
    
    # === HYBRID TRANSCRIPTION SYSTEM ===
    # Enable hybrid transcription for improved accuracy
    HYBRID_TRANSCRIPTION_ENABLED = os.environ.get('HYBRID_TRANSCRIPTION_ENABLED', 'true').lower() == 'true'
    
    # Confidence threshold for retry with larger model (0.0 - 1.0)
    # Segments below this threshold will be re-transcribed
    CONFIDENCE_RETRY_THRESHOLD = float(os.environ.get('CONFIDENCE_RETRY_THRESHOLD', 0.7))
    
    # Model to use for retry (larger = more accurate but slower)
    RETRY_MODEL = os.environ.get('RETRY_MODEL', 'large-v3')
    RETRY_BEAM_SIZE = int(os.environ.get('RETRY_BEAM_SIZE', 5))  # Higher beam = more accurate
    
    # Dual-model comparison for short videos (compare 2 transcriptions, pick best)
    DUAL_MODEL_ENABLED = os.environ.get('DUAL_MODEL_ENABLED', 'true').lower() == 'true'
    DUAL_MODEL_MAX_DURATION = int(os.environ.get('DUAL_MODEL_MAX_DURATION', 600))  # Max 10 minutes for dual-model
    DUAL_MODEL_SECONDARY = os.environ.get('DUAL_MODEL_SECONDARY', 'large-v3-turbo')
    
    # Groq API fallback (free tier: 14,400 requests/day)
    GROQ_API_ENABLED = os.environ.get('GROQ_API_ENABLED', 'true').lower() == 'true'
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    GROQ_MODEL = os.environ.get('GROQ_MODEL', 'whisper-large-v3-turbo')  # Options: whisper-large-v3, whisper-large-v3-turbo
    GROQ_FALLBACK_ON_LOW_CONFIDENCE = os.environ.get('GROQ_FALLBACK_ON_LOW_CONFIDENCE', 'true').lower() == 'true'
    GROQ_CONFIDENCE_THRESHOLD = float(os.environ.get('GROQ_CONFIDENCE_THRESHOLD', 0.6))  # Use Groq if below this
    
    # Minimum segment confidence to consider "good enough"
    MIN_SEGMENT_CONFIDENCE = float(os.environ.get('MIN_SEGMENT_CONFIDENCE', 0.5))
    
    PROCESSING_CONCURRENCY = int(os.environ.get('PROCESSING_CONCURRENCY', 1))
    PROCESSING_COOLDOWN_SECONDS = float(os.environ.get('PROCESSING_COOLDOWN_SECONDS', 1))  # Reduced from 2
    EXPORT_THROTTLE_SECONDS = float(os.environ.get('EXPORT_THROTTLE_SECONDS', 0))  # Disabled for parallel export
    
    # Long video thresholds for special handling of podcasts > 1 hour
    LONG_VIDEO_THRESHOLD = int(os.environ.get('LONG_VIDEO_THRESHOLD', 3600))  # 1 hour
    VERY_LONG_VIDEO_THRESHOLD = int(os.environ.get('VERY_LONG_VIDEO_THRESHOLD', 7200))  # 2 hours
    
    # Clip generation settings - OPTIMIZED FOR MONOLOG/PODCAST
    CLIP_DURATIONS = [
        (9, 15),   # Short clips
        (18, 22),  # Medium clips
        (28, 35),  # Long clips - extended upper bound
        (40, 55),  # Extended clips - for context-rich podcast content
    ]
    MIN_CLIP_DURATION = 8  # Lowered from 9 for more flexibility
    MAX_CLIP_DURATION = 55  # Increased from 35 for extended clips
    
    # Scoring thresholds - VERY LENIENT for monolog/podcast support
    MIN_VIRAL_SCORE = 0.08  # Lowered further for monolog
    MAX_CLIPS_PER_VIDEO = int(os.environ.get('MAX_CLIPS_PER_VIDEO', 30))  # Increased for very long videos (>1hr)
    TARGET_CLIP_COUNT = int(os.environ.get('TARGET_CLIP_COUNT', 15))  # Increased for long podcasts
    MIN_CLIP_OUTPUT = int(os.environ.get('MIN_CLIP_OUTPUT', 5))  # Ensure at least 5 clips per run
    FORCED_MIN_CLIP_OUTPUT = int(os.environ.get('FORCED_MIN_CLIP_OUTPUT', 5))  # Hard guarantee for monologs
    LONG_VIDEO_MIN_CLIPS = int(os.environ.get('LONG_VIDEO_MIN_CLIPS', 10))  # Min clips for videos >1hr
    VERY_LONG_VIDEO_MIN_CLIPS = int(os.environ.get('VERY_LONG_VIDEO_MIN_CLIPS', 20))  # Min clips for videos >2hr
    RELAXED_VIRAL_SCORE = float(os.environ.get('RELAXED_VIRAL_SCORE', 0.03))  # Even more relaxed
    FALLBACK_VIRAL_SCORE = float(os.environ.get('FALLBACK_VIRAL_SCORE', 0.0))  # Zero threshold for fallback
    MIN_CLIP_GAP_SECONDS = float(os.environ.get('MIN_CLIP_GAP_SECONDS', 1.5))  # Further reduced gap
    MAX_CLIP_OVERLAP_RATIO = float(os.environ.get('MAX_CLIP_OVERLAP_RATIO', 0.75))  # Allow more overlap for variety
    
    # Scene detection - ULTRA SENSITIVE for monolog/podcast
    SCENE_THRESHOLD = 12.0  # Lowered further for monolog detection
    MIN_SCENE_LENGTH = 1  # Allow even short scenes
    
    # === DEEP LEARNING VIDEO ANALYSIS ===
    # Enable advanced video analysis with MediaPipe + YOLO
    ENABLE_DEEP_LEARNING_VIDEO = os.environ.get('ENABLE_DEEP_LEARNING_VIDEO', 'true').lower() == 'true'
    
    # MediaPipe Face Detection
    MEDIAPIPE_FACE_CONFIDENCE = float(os.environ.get('MEDIAPIPE_FACE_CONFIDENCE', 0.5))
    
    # YOLOv8 Object Detection
    # Model sizes: 'n' (nano/fastest), 's' (small), 'm' (medium), 'l' (large), 'x' (xlarge/best)
    YOLO_MODEL_SIZE = os.environ.get('YOLO_MODEL_SIZE', 'n')
    YOLO_CONFIDENCE = float(os.environ.get('YOLO_CONFIDENCE', 0.5))
    
    # Speaker Activity Detection
    SPEAKER_TALKING_THRESHOLD = float(os.environ.get('SPEAKER_TALKING_THRESHOLD', 0.3))  # Mouth open ratio to consider "talking"
    SPEAKER_ENGAGEMENT_THRESHOLD = float(os.environ.get('SPEAKER_ENGAGEMENT_THRESHOLD', 0.2))  # Expression threshold
    
    # Audio analysis
    SILENCE_THRESHOLD = -40  # dB
    MIN_SILENCE_DURATION = 1000  # milliseconds
    
    # Filler words to remove (Indonesian & English)
    FILLER_WORDS = [
        'ehm', 'emm', 'umm', 'uh', 'um',
        'anu', 'jadi', 'gitu', 'kayak',
        'seperti', 'terus', 'nah', 'ya kan',
        'like', 'you know', 'i mean', 'basically'
    ]
    
    # Viral indicators (keywords that suggest engaging content)
    VIRAL_KEYWORDS = {
        'hook': [
            'rahasia', 'secret', 'truth', 'fakta', 'fact',
            'shocking', 'mengejutkan', 'gak nyangka', 'ternyata',
            'jangan', 'never', 'harus', 'must', 'wajib',
            'dengerin', 'perhatikan', 'listen', 'watch out',
            'bongkar', 'reveal', 'bocor', 'leak', 'exposed',
            'terbukti', 'proven', 'pasti', 'definitely',
            'catet', 'catat', 'note', 'ingat', 'remember',
            'brutal', 'savage', 'mentah', 'telanjang', 'blak-blakan',
            'stop', 'quit', 'selesai', 'cukup', 'enough'
        ],
        'emotional': [
            'gagal', 'failed', 'sukses', 'success', 'menang', 'kalah',
            'sedih', 'bahagia', 'marah', 'kecewa', 'bangga',
            'sad', 'happy', 'angry', 'proud', 'disappointed',
            'hancur', 'destroyed', 'ambyar', 'terpukul', 'down',
            'naik', 'rise', 'meledak', 'explode', 'boom',
            'gelisah', 'anxious', 'takut', 'scared', 'berani', 'brave',
            'nyerah', 'give up', 'lawan', 'fight', 'perjuangan', 'struggle'
        ],
        'controversial': [
            'kontroversial', 'controversial', 'debat', 'debate',
            'salah', 'wrong', 'benar', 'right', 'bohong', 'lie',
            'jujur', 'honest', 'truth', 'kebohongan',
            'problematik', 'problematic', 'toxic', 'racun',
            'penipu', 'scam', 'scammer', 'tipu-tipu',
            'konspirasi', 'conspiracy', 'tersembunyi', 'hidden',
            'manipulasi', 'manipulate', 'dipermainkan', 'played'
        ],
        'educational': [
            'cara', 'how to', 'tips', 'trik', 'trick',
            'tutorial', 'belajar', 'learn', 'pelajaran',
            'lesson', 'panduan', 'guide',
            'strategi', 'strategy', 'teknik', 'technique',
            'metode', 'method', 'sistem', 'system',
            'formula', 'rumus', 'blueprint', 'framework',
            'step', 'langkah', 'tahap', 'phase'
        ],
        'entertaining': [
            'lucu', 'funny', 'ngakak', 'hilarious',
            'kocak', 'gokil', 'epic', 'amazing',
            'gila', 'crazy', 'insane',
            'absurd', 'aneh', 'weird', 'unik', 'unique',
            'tak terduga', 'unexpected', 'plot twist',
            'dramatis', 'dramatic', 'spektakuler', 'spectacular'
        ],
        'money': [
            'cuan', 'uang', 'money', 'duit', 'cash',
            'omset', 'omzet', 'revenue', 'profit', 'untung',
            'gaji', 'salary', 'income', 'penghasilan',
            'closing', 'deal', 'sales', 'penjualan',
            'investasi', 'investment', 'passive income',
            'bonus', 'komisi', 'commission', 'fee'
        ],
        'urgency': [
            'sekarang', 'now', 'segera', 'immediately',
            'cepat', 'fast', 'quick', 'langsung', 'directly',
            'deadline', 'terbatas', 'limited', 'eksklusif', 'exclusive',
            'hari ini', 'today', 'malam ini', 'tonight',
            'nunda', 'delay', 'terlambat', 'late', 'ketinggalan', 'miss out'
        ]
    }

    # Meta topics that frequently go viral (Timoty playbook)
    META_TOPICS = {
        'youth_mistakes': {
            'label': 'Kesalahan Anak Muda',
            'keywords': [
                'anak', 'muda', 'genz', 'gen-z', 'gen z', 'pemula', 'baru mulai',
                'bar bar', 'barbar', 'ceroboh', 'grasa grusu', 'grusak grusuk',
                'impulsif', 'sok cepat', 'ikut trend', 'ikut-ikutan'
            ]
        },
        'money_poverty': {
            'label': 'Uang dan Kemiskinan',
            'keywords': [
                'miskin', 'bokek', 'duit', 'uang', 'krisis', 'bangkrut',
                'fakir', 'sultan', 'tajir', 'kekayaan', 'pas-pasan', 'utang',
                'cicilan', 'rekening', 'dompet'
            ]
        },
        'discipline_lazy': {
            'label': 'Disiplin vs Malas',
            'keywords': [
                'malas', 'mager', 'rebahan', 'tidur', 'bangun siang',
                'disiplin', 'kebiasaan', 'consistency', 'rutinitas',
                'latihan', 'habit'
            ]
        },
        'mental_slap': {
            'label': 'Mental Slap',
            'keywords': [
                'tampar', 'mental', 'pahit', 'sadis', 'sadar', 'wake up',
                'ngegas', 'keras', 'jleb', 'perih'
            ]
        },
        'relationship_business': {
            'label': 'Relationship & Bisnis',
            'keywords': [
                'relasi', 'network', 'jaringan', 'partner', 'tim', 'team',
                'toxic friend', 'teman toxic', 'klien', 'client', 'bisnis',
                'relationship', 'komunitas'
            ]
        },
        'harsh_truth': {
            'label': 'Kenyataan Pahit',
            'keywords': [
                'kenyataan', 'realita', 'pahit', 'jujur', 'sadis', 'fakta pahit',
                'truth hurts', 'real talk'
            ]
        },
        'poor_vs_success': {
            'label': 'Miskin vs Sukses',
            'keywords': [
                'miskin', 'sukses', 'berhasil', 'kelas bawah', 'kelas atas',
                'naik kelas', 'bangkit', 'zero to hero', 'kelas menengah'
            ]
        },
        'life_paradox': {
            'label': 'Paradoks Hidup',
            'keywords': [
                'paradoks', 'kontradiksi', 'balik fakta', 'double standard',
                'aneh', 'tidak masuk akal', 'mind twist'
            ]
        },
        'rich_mindset': {
            'label': 'Mindset Kaya',
            'keywords': [
                'mindset', 'kaya', 'wealth', 'wealthy', 'millionaire',
                'milyarder', 'cashflow', 'passive income', 'asset', 'aset'
            ]
        },
        # KALIMASADA (Prof Kaka) Meta Topics
        'crypto_trading': {
            'label': 'Crypto Trading',
            'keywords': [
                'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'kripto',
                'trading', 'trader', 'entry', 'exit', 'stop loss', 'take profit',
                'bullish', 'bearish', 'pump', 'dump', 'altcoin', 'defi'
            ]
        },
        'technical_analysis': {
            'label': 'Analisis Teknikal',
            'keywords': [
                'support', 'resistance', 'trend', 'chart', 'candle', 'candlestick',
                'rsi', 'macd', 'moving average', 'fibonacci', 'breakout', 'reversal',
                'volume', 'indikator', 'pattern', 'pola'
            ]
        },
        'risk_management': {
            'label': 'Risk Management',
            'keywords': [
                'risk', 'resiko', 'management', 'position size', 'lot',
                'money management', 'modal', 'margin', 'leverage', 'portfolio',
                'diversifikasi', 'alokasi', 'risk reward'
            ]
        },
        'trading_psychology': {
            'label': 'Psikologi Trading',
            'keywords': [
                'fomo', 'fear', 'greed', 'emosi', 'psikologi', 'sabar', 'patience',
                'disiplin', 'mental', 'cut loss', 'take profit', 'hold',
                'panic sell', 'rational', 'rasional'
            ]
        }
    }

    # Topics that rarely go viral (penalty)
    RARE_TOPICS = [
        'grafik', 'chart', 'spreadsheet', 'excel', 'data', 'dataset',
        'statistik', 'statistic', 'crypto', 'coin', 'token', 'candlestick',
        'whitepaper', 'algoritma', 'teknis', 'technical', 'diagram',
        'infografis', 'mata uang kripto', 'analisis fundamental',
        'analisis teknikal', 'pitch deck'
    ]

    # Relatability / mental slap triggers
    MENTAL_SLAP_KEYWORDS = [
        'malas', 'pemalas', 'mager', 'rebahan', 'insecure', 'takut gagal',
        'takut ditolak', 'toxic friend', 'teman toxic', 'kerja keras',
        'terlalu nyaman', 'zona nyaman', 'tanggung jawab', 'lamban',
        'penakut', 'penunda', 'overthinking'
    ]

    # Text flash (FAKTOR 11) overlay configuration
    TEXT_FLASH_ENABLED = True
    TEXT_FLASH_DURATION = 0.8  # seconds
    TEXT_FLASH_FONT_SIZE = 72
    TEXT_FLASH_FONT_COLOR = 'white'
    TEXT_FLASH_BG_COLOR = 'black@0.8'
    TEXT_FLASH_POSITION = 'center'  # top, center, bottom
    MAX_TEXT_FLASH_PER_CLIP = 3
    TEXT_FLASH_VOCAB = [
        'miskin', 'gagal', 'paradoks', 'diam bro', 'denger dulu', 'mental slap',
        'bangkrut', 'toxic', 'sadis', 'malas', 'insecure', 'kerja keras',
        'tanggung jawab', 'bangun', 'disiplin'
    ]
    
    # Video export settings - Configurable via environment
    # Default: GPU encoding if available, falls back to CPU
    VIDEO_CODEC = os.environ.get('VIDEO_CODEC', 'h264_nvenc')  # 'h264_nvenc' for GPU, 'libx264' for CPU
    # ALTERNATIVE: 'hevc_nvenc' for better compression (smaller file size, same quality)
    AUDIO_CODEC = 'aac'
    VIDEO_BITRATE = '1M'  # Lower bitrate for smaller file size
    AUDIO_BITRATE = '192k'  # Better audio quality
    OUTPUT_FORMAT = 'mp4'
    
    # GPU Acceleration settings - Configurable via environment
    # Set USE_GPU_ACCELERATION=false in .env if FFmpeg NVENC doesn't work
    USE_GPU_ACCELERATION = os.environ.get('USE_GPU_ACCELERATION', 'true').lower() == 'true'
    GPU_DEVICE = int(os.environ.get('GPU_DEVICE', 0))  # Default GPU device (0 for first GPU)
    NVENC_PRESET = os.environ.get('NVENC_PRESET', 'medium')  # Options: slow, medium, fast
    NVENC_RC_MODE = 'vbr'  # Rate control: vbr (variable), cbr (constant), cqp (fixed QP)
    NVENC_QUALITY = 25  # Quality (0=best, 51=worst) for CQP mode
    HWACCEL_DECODER = os.environ.get('HWACCEL_DECODER', 'cuda')  # Hardware-accelerated decoding
    HWACCEL_OUTPUT_FORMAT = 'cuda'  # Keep frames on GPU to reduce memory transfers
    
    # CPU Encoding settings (used when GPU not available)
    FFMPEG_THREADS = int(os.environ.get('FFMPEG_THREADS', 8))  # Number of threads for CPU encoding
    CPU_PRESET = os.environ.get('CPU_PRESET', 'fast')  # libx264 preset: ultrafast, fast, medium, slow
    
    # GPU Filter Processing - Use CUDA filters for speed
    USE_GPU_FILTERS = False  # Disable GPU filters due to compatibility issues, use CPU filters instead
    SCALE_FILTER = 'scale'  # Use CPU-based scale (compatible with all codecs)
    
    # Batch processing for parallel clip export
    ENABLE_BATCH_EXPORT = True  # Process multiple clips in parallel
    # Auto-detect optimal parallel exports based on CPU cores
    import multiprocessing
    _cpu_count = multiprocessing.cpu_count()
    MAX_PARALLEL_EXPORTS = int(os.environ.get('MAX_PARALLEL_EXPORTS', min(4, max(2, _cpu_count // 2))))  # Use half of CPU cores, min 2, max 4
    
    # Aspect ratio settings (16:9 for viral content)
    TARGET_ASPECT_RATIO = '16:9'
    
    # Resolution presets - user can select in frontend
    RESOLUTION_PRESETS = {
        '720p': {'width': 1280, 'height': 720, 'bitrate': '1M'},
        '1080p': {'width': 1920, 'height': 1080, 'bitrate': '2M'}
    }
    DEFAULT_RESOLUTION = '1080p'
    
    # Default resolution (can be overridden per-job)
    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080
    
    # Hook overlay settings
    HOOK_ENABLED = True  # Enable automatic hook overlay
    HOOK_DURATION = 1.2  # Preferred duration (seconds) within 0.5-1.5 range
    HOOK_MIN_DURATION = 0.5  # Minimum hook display (seconds)
    HOOK_MAX_DURATION = 1.5  # Preferred maximum (hard-clamped at 2s in runtime)
    HOOK_FONT_SIZE = 48
    HOOK_FONT_COLOR = 'white'
    HOOK_BG_COLOR = 'black@0.7'  # Semi-transparent black background
    HOOK_POSITION = 'center'  # Position: top, center, bottom
    HOOK_ANIMATION = 'fade'  # Animation: fade, slide, none
    
    # Create folders if not exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
