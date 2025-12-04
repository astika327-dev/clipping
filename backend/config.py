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
    MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    MAX_VIDEO_DURATION = 3600  # 60 minutes in seconds
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
    
    # Transcription settings
    TRANSCRIPTION_BACKEND = os.environ.get('TRANSCRIPTION_BACKEND', 'faster-whisper')
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'tiny')  # tiny, base, small, medium, large
    WHISPER_LANGUAGE = os.environ.get('WHISPER_LANGUAGE', 'id')  # Default: Indonesian
    FASTER_WHISPER_MODEL = os.environ.get('FASTER_WHISPER_MODEL', 'tiny')
    FASTER_WHISPER_DEVICE = os.environ.get('FASTER_WHISPER_DEVICE', 'cpu')
    FASTER_WHISPER_COMPUTE_TYPE = os.environ.get('FASTER_WHISPER_COMPUTE_TYPE', 'int8_float16')
    FASTER_WHISPER_BEAM_SIZE = int(os.environ.get('FASTER_WHISPER_BEAM_SIZE', 1))
    FASTER_WHISPER_CHUNK_LENGTH = int(os.environ.get('FASTER_WHISPER_CHUNK_LENGTH', 30))
    PROCESSING_CONCURRENCY = int(os.environ.get('PROCESSING_CONCURRENCY', 1))
    PROCESSING_COOLDOWN_SECONDS = float(os.environ.get('PROCESSING_COOLDOWN_SECONDS', 2))
    EXPORT_THROTTLE_SECONDS = float(os.environ.get('EXPORT_THROTTLE_SECONDS', 0.5))
    
    # Clip generation settings
    CLIP_DURATIONS = [
        (9, 15),   # Short clips
        (18, 22),  # Medium clips
        (28, 32),  # Long clips
    ]
    MIN_CLIP_DURATION = 9
    MAX_CLIP_DURATION = 35
    
    # Scoring thresholds
    MIN_VIRAL_SCORE = 0.5  # 0.0 to 1.0
    MAX_CLIPS_PER_VIDEO = 10
    
    # Scene detection
    SCENE_THRESHOLD = 27.0  # Lower = more sensitive
    MIN_SCENE_LENGTH = 3  # Minimum scene length in seconds
    
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
            'jangan', 'never', 'harus', 'must', 'wajib'
        ],
        'emotional': [
            'gagal', 'failed', 'sukses', 'success', 'menang', 'kalah',
            'sedih', 'bahagia', 'marah', 'kecewa', 'bangga',
            'sad', 'happy', 'angry', 'proud', 'disappointed'
        ],
        'controversial': [
            'kontroversial', 'controversial', 'debat', 'debate',
            'salah', 'wrong', 'benar', 'right', 'bohong', 'lie',
            'jujur', 'honest', 'truth', 'kebohongan'
        ],
        'educational': [
            'cara', 'how to', 'tips', 'trik', 'trick',
            'tutorial', 'belajar', 'learn', 'pelajaran',
            'lesson', 'panduan', 'guide'
        ],
        'entertaining': [
            'lucu', 'funny', 'ngakak', 'hilarious',
            'kocak', 'gokil', 'epic', 'amazing',
            'gila', 'crazy', 'insane'
        ]
    }
    
    # Video export settings
    VIDEO_CODEC = 'libx264'
    AUDIO_CODEC = 'aac'
    VIDEO_BITRATE = '2M'
    AUDIO_BITRATE = '128k'
    OUTPUT_FORMAT = 'mp4'
    
    # Create folders if not exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
