"""
Audio Analyzer Module
Handles audio transcription and content analysis using Whisper
"""
import re
from typing import List, Dict, Tuple, Optional

import numpy as np

try:
    import whisper
except ImportError:  # pragma: no cover - whisper installed via requirements
    whisper = None

try:
    from faster_whisper import WhisperModel as FasterWhisperModel
except ImportError:  # pragma: no cover - optional dependency
    FasterWhisperModel = None

class AudioAnalyzer:
    def __init__(self, video_path: str, config, overrides: Optional[Dict[str, str]] = None):
        self.video_path = video_path
        self.config = config
        self.model = None
        self.transcript = None
        self.faster_model = None
        overrides = overrides or {}

        default_backend = getattr(config, 'TRANSCRIPTION_BACKEND', 'openai-whisper')
        self.backend = overrides.get('transcription_backend', default_backend)
        self.backend = (self.backend or default_backend).lower()

        self.whisper_model_name = overrides.get('whisper_model', getattr(config, 'WHISPER_MODEL', 'tiny'))
        self.faster_model_name = overrides.get('faster_whisper_model', getattr(config, 'FASTER_WHISPER_MODEL', 'tiny'))
        self.faster_device = overrides.get('faster_whisper_device', getattr(config, 'FASTER_WHISPER_DEVICE', 'cpu'))
        self.faster_compute_type = overrides.get('faster_whisper_compute_type', getattr(config, 'FASTER_WHISPER_COMPUTE_TYPE', 'int8_float16'))
        
    def analyze(self, language: str = 'id') -> Dict:
        """
        Main analysis function
        Returns transcription and content analysis
        """
        model_name = self.faster_model_name if self.backend == 'faster-whisper' else self.whisper_model_name
        backend_label = 'Faster-Whisper' if self.backend == 'faster-whisper' else 'openai-whisper'
        print(f"🎤 Analyzing audio with Whisper ({model_name} via {backend_label})...")
        
        # Load model lazily depending on backend
        transcript = self._transcribe(language)
        
        # Analyze content
        content_analysis = self._analyze_content(transcript)
        
        return {
            'transcript': transcript,
            'analysis': content_analysis
        }
    
    def _load_openai_whisper_model(self):
        """Load classic openai/whisper model."""
        if whisper is None:
            raise ImportError("openai-whisper is not installed")
        if self.model is None:
            print(f"📥 Loading Whisper model: {self.whisper_model_name}")
            self.model = whisper.load_model(self.whisper_model_name)
            print("✅ Model loaded")

    def _load_faster_whisper_model(self):
        """Load faster-whisper model for efficient CPU inference."""
        if FasterWhisperModel is None:
            raise ImportError("faster-whisper is not installed")
        if self.faster_model is None:
            print(
                f"⚡ Loading Faster-Whisper model: {self.faster_model_name}"
                f" [{self.faster_device} / {self.faster_compute_type}]"
            )
            self.faster_model = FasterWhisperModel(
                self.faster_model_name,
                device=self.faster_device,
                compute_type=self.faster_compute_type
            )
            print("✅ Faster-Whisper model ready")
    
    def _transcribe(self, language: str) -> Dict:
        """Dispatch transcription to the configured backend."""
        if self.backend == 'faster-whisper':
            try:
                return self._transcribe_with_faster_whisper(language)
            except Exception as exc:
                print(f"⚠️ Faster-Whisper failed ({exc}). Falling back to openai-whisper.")
                self.backend = 'openai-whisper'
        return self._transcribe_with_openai_whisper(language)

    def _ensure_video_ready(self):
        import os
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found at: {self.video_path}")
        print(f"   Video path: {self.video_path}")
        import shutil
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            print("❌ WARNING: FFmpeg not found in PATH!")
            if os.path.exists('ffmpeg.exe'):
                os.environ['PATH'] += os.pathsep + os.getcwd()
            else:
                raise FileNotFoundError("FFmpeg not found. Please install FFmpeg and add to PATH.")
        else:
            print(f"   FFmpeg found at: {ffmpeg_path}")

    def _transcribe_with_openai_whisper(self, language: str) -> Dict:
        print("🎯 Transcribing audio with openai-whisper...")
        self._ensure_video_ready()
        self._load_openai_whisper_model()

        result = self.model.transcribe(
            self.video_path,
            language=language,
            task='transcribe',
            verbose=False,
            fp16=False
        )

        segments = []
        for segment in result['segments']:
            segments.append({
                'id': segment['id'],
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'words': self._extract_words(segment['text'])
            })

        print(f"✅ Transcribed {len(segments)} segments")

        return {
            'language': result.get('language', language),
            'text': result['text'],
            'segments': segments
        }

    def _transcribe_with_faster_whisper(self, language: str) -> Dict:
        print("⚡ Transcribing audio with Faster-Whisper...")
        self._ensure_video_ready()
        self._load_faster_whisper_model()

        segments_iter, info = self.faster_model.transcribe(
            self.video_path,
            language=language,
            beam_size=self.config.FASTER_WHISPER_BEAM_SIZE,
            chunk_length=self.config.FASTER_WHISPER_CHUNK_LENGTH,
            word_timestamps=False
        )

        segments = []
        for idx, segment in enumerate(segments_iter):
            text = segment.text.strip()
            segments.append({
                'id': idx,
                'start': segment.start,
                'end': segment.end,
                'text': text,
                'words': self._extract_words(text)
            })

        print(f"✅ Faster-Whisper produced {len(segments)} segments")

        return {
            'language': getattr(info, 'language', language),
            'text': ' '.join(seg['text'] for seg in segments),
            'segments': segments
        }
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract clean words from text"""
        # Remove punctuation and convert to lowercase
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    def _analyze_content(self, transcript: Dict) -> Dict:
        """
        Analyze transcript content for viral potential
        """
        print("🧠 Analyzing content...")
        
        segments = transcript['segments']
        
        # Analyze each segment
        segment_scores = []
        for segment in segments:
            score = self._score_segment(segment)
            segment_scores.append({
                'segment_id': segment['id'],
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'],
                'scores': score
            })
        
        # Find hooks (strong opening statements)
        hooks = self._find_hooks(segments)
        
        # Find punchlines (impactful statements)
        punchlines = self._find_punchlines(segments)
        
        # Overall content analysis
        overall = self._calculate_overall_scores(segment_scores)
        
        return {
            'segment_scores': segment_scores,
            'hooks': hooks,
            'punchlines': punchlines,
            'overall': overall
        }
    
    def _score_segment(self, segment: Dict) -> Dict:
        """
        Score a single segment for various qualities
        """
        text = segment['text'].lower()
        words = segment['words']
        
        # Check for viral keywords
        hook_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS['hook'])
        emotional_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS['emotional'])
        controversial_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS['controversial'])
        educational_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS['educational'])
        entertaining_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS['entertaining'])
        
        # Check for filler words (negative score)
        filler_count = sum(1 for word in words if word in self.config.FILLER_WORDS)
        filler_penalty = min(filler_count * 0.1, 0.5)
        
        # Check for questions (engaging)
        has_question = '?' in segment['text']
        question_bonus = 0.2 if has_question else 0
        
        # Check for numbers/stats (credibility)
        has_numbers = bool(re.search(r'\d+', segment['text']))
        numbers_bonus = 0.15 if has_numbers else 0
        
        # Calculate total engagement score
        engagement = (
            hook_score * 0.25 +
            emotional_score * 0.20 +
            controversial_score * 0.15 +
            educational_score * 0.15 +
            entertaining_score * 0.15 +
            question_bonus +
            numbers_bonus -
            filler_penalty
        )
        
        engagement = max(0, min(1, engagement))  # Clamp to 0-1
        
        return {
            'hook': hook_score,
            'emotional': emotional_score,
            'controversial': controversial_score,
            'educational': educational_score,
            'entertaining': entertaining_score,
            'engagement': engagement,
            'has_question': has_question,
            'has_numbers': has_numbers,
            'filler_count': filler_count
        }
    
    def _check_keywords(self, words: List[str], keywords: List[str]) -> float:
        """
        Check how many keywords are present
        Returns score 0-1
        """
        matches = sum(1 for word in words if word in keywords)
        # Normalize: 3+ matches = max score
        return min(matches / 3.0, 1.0)
    
    def _find_hooks(self, segments: List[Dict]) -> List[Dict]:
        """
        Find potential hooks (strong opening statements)
        Usually in first 10 seconds or after scene changes
        """
        hooks = []
        
        for segment in segments[:5]:  # Check first 5 segments
            words = segment['words']
            
            # Check for hook keywords
            hook_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS['hook'])
            
            if hook_score > 0.3:
                hooks.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'],
                    'score': hook_score
                })
        
        return sorted(hooks, key=lambda x: x['score'], reverse=True)
    
    def _find_punchlines(self, segments: List[Dict]) -> List[Dict]:
        """
        Find punchlines (impactful statements)
        """
        punchlines = []
        
        for segment in segments:
            text = segment['text']
            words = segment['words']
            
            # Punchlines often have:
            # - Emotional words
            # - Controversial statements
            # - Surprising facts
            # - Strong opinions
            
            emotional = self._check_keywords(words, self.config.VIRAL_KEYWORDS['emotional'])
            controversial = self._check_keywords(words, self.config.VIRAL_KEYWORDS['controversial'])
            
            punchline_score = (emotional + controversial) / 2
            
            # Also check for exclamation marks
            if '!' in text:
                punchline_score += 0.2
            
            if punchline_score > 0.4:
                punchlines.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'],
                    'score': punchline_score
                })
        
        return sorted(punchlines, key=lambda x: x['score'], reverse=True)
    
    def _calculate_overall_scores(self, segment_scores: List[Dict]) -> Dict:
        """
        Calculate overall content scores
        """
        if not segment_scores:
            return {}
        
        # Average scores
        avg_engagement = np.mean([s['scores']['engagement'] for s in segment_scores])
        avg_hook = np.mean([s['scores']['hook'] for s in segment_scores])
        avg_emotional = np.mean([s['scores']['emotional'] for s in segment_scores])
        
        # Determine dominant category
        categories = {
            'educational': np.mean([s['scores']['educational'] for s in segment_scores]),
            'entertaining': np.mean([s['scores']['entertaining'] for s in segment_scores]),
            'controversial': np.mean([s['scores']['controversial'] for s in segment_scores]),
            'emotional': avg_emotional
        }
        
        dominant_category = max(categories.items(), key=lambda x: x[1])[0]
        
        return {
            'avg_engagement': float(avg_engagement),
            'avg_hook_strength': float(avg_hook),
            'avg_emotional': float(avg_emotional),
            'dominant_category': dominant_category,
            'category_scores': {k: float(v) for k, v in categories.items()}
        }
