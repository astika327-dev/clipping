"""
Audio Analyzer Module
Handles audio transcription and content analysis using Whisper
"""
import re
from typing import List, Dict, Tuple, Optional

import numpy as np

try:
    import torch
except ImportError:  # pragma: no cover - torch optional in some environments
    torch = None

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
        self.whisper_fallback_model = overrides.get(
            'whisper_fallback_model', getattr(config, 'WHISPER_FALLBACK_MODEL', 'base')
        )
        self.faster_model_name = overrides.get('faster_whisper_model', getattr(config, 'FASTER_WHISPER_MODEL', 'tiny'))
        self.faster_fallback_model = overrides.get(
            'faster_whisper_fallback_model', getattr(config, 'FASTER_WHISPER_FALLBACK_MODEL', 'base')
        )
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
            try:
                self.model = whisper.load_model(self.whisper_model_name)
                print("✅ Model loaded")
            except Exception as exc:
                if self.whisper_model_name == self.whisper_fallback_model:
                    print(f"❌ Failed to load Whisper model {self.whisper_model_name}: {exc}")
                    raise
                print(
                    f"⚠️ Failed to load Whisper model '{self.whisper_model_name}' ({exc}). "
                    f"Falling back to '{self.whisper_fallback_model}'."
                )
                self.whisper_model_name = self.whisper_fallback_model
                self.model = whisper.load_model(self.whisper_model_name)
                print("✅ Fallback Whisper model loaded")

    def _load_faster_whisper_model(self):
        """Load faster-whisper model for efficient CPU inference."""
        if FasterWhisperModel is None:
            raise ImportError("faster-whisper is not installed")
        if self.faster_model is None:
            print(
                f"⚡ Loading Faster-Whisper model: {self.faster_model_name}"
                f" [{self.faster_device} / {self.faster_compute_type}]"
            )
            try:
                self.faster_model = FasterWhisperModel(
                    self.faster_model_name,
                    device=self.faster_device,
                    compute_type=self.faster_compute_type
                )
                print("✅ Faster-Whisper model ready")
            except Exception as exc:
                if self.faster_model_name == self.faster_fallback_model:
                    print(f"❌ Failed to load Faster-Whisper model {self.faster_model_name}: {exc}")
                    raise
                print(
                    f"⚠️ Failed to load Faster-Whisper model '{self.faster_model_name}' ({exc}). "
                    f"Falling back to '{self.faster_fallback_model}'."
                )
                self.faster_model_name = self.faster_fallback_model
                self.faster_model = FasterWhisperModel(
                    self.faster_model_name,
                    device=self.faster_device,
                    compute_type=self.faster_compute_type
                )
                print("✅ Fallback Faster-Whisper model ready")
    
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

        # Calculate adaptive timeout: 2x video duration + 5min buffer (minimum 10min)
        duration = self._get_video_duration_fallback()
        timeout_seconds = max(int(duration * 2) + 300, 600)  # Min 10 minutes
        print(f"   ⏱  Transcription timeout set to: {timeout_seconds}s ({timeout_seconds/60:.1f} min)")

        # Use threading for timeout control (works on Windows)
        import threading
        
        result_container = {'result': None, 'error': None}
        
        def transcribe_worker():
            try:
                result_container['result'] = self.model.transcribe(
                    self.video_path,
                    language=language,
                    task='transcribe',
                    verbose=False,
                    fp16=False
                )
            except Exception as e:
                result_container['error'] = e
        
        # Start transcription in thread
        thread = threading.Thread(target=transcribe_worker, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            # Timeout occurred
            print(f"⚠️  Whisper timeout after {timeout_seconds}s! Attempting chunk-based processing...")
            # Note: We can't kill the thread, but we can process in chunks instead
            return self._transcribe_in_chunks_openai(language, chunk_duration=300)
        
        if result_container['error']:
            raise result_container['error']
        
        result = result_container['result']
        if not result:
            raise RuntimeError("Transcription failed without error")

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
        """
        Transcribe using Faster-Whisper with optimizations:
        - VAD filter to skip silent parts (30-50% faster)
        - Optimized beam_size for speed
        - Guaranteed minimum segments for monolog
        """
        print("⚡ Transcribing audio with Faster-Whisper (VAD optimized)...")
        self._ensure_video_ready()
        self._load_faster_whisper_model()
        
        # Get beam_size from config, default to 1 for speed
        beam_size = getattr(self.config, 'FASTER_WHISPER_BEAM_SIZE', 1)
        chunk_length = getattr(self.config, 'FASTER_WHISPER_CHUNK_LENGTH', 30)
        
        # Enable VAD filter for faster processing (skip silent parts)
        vad_filter = getattr(self.config, 'FASTER_WHISPER_VAD_FILTER', True)
        
        print(f"   📊 Settings: beam_size={beam_size}, chunk_length={chunk_length}, vad_filter={vad_filter}")

        try:
            segments_iter, info = self.faster_model.transcribe(
                self.video_path,
                language=language,
                beam_size=beam_size,
                chunk_length=chunk_length,
                word_timestamps=False,
                vad_filter=vad_filter,  # Skip silent parts for speed
                vad_parameters=dict(
                    min_silence_duration_ms=500,  # Min silence to consider
                    speech_pad_ms=200,  # Padding around speech
                ) if vad_filter else None
            )
        except TypeError:
            # Fallback if VAD parameters not supported in this version
            print("   ⚠️ VAD parameters not supported, using basic transcription")
            segments_iter, info = self.faster_model.transcribe(
                self.video_path,
                language=language,
                beam_size=beam_size,
                chunk_length=chunk_length,
                word_timestamps=False
            )

        segments = []
        segment_count = 0
        last_progress_report = 0
        
        for idx, segment in enumerate(segments_iter):
            text = segment.text.strip()
            if not text:  # Skip empty segments
                continue
                
            segments.append({
                'id': idx,
                'start': segment.start,
                'end': segment.end,
                'text': text,
                'words': self._extract_words(text)
            })
            segment_count += 1
            
            # Progress reporting every 20 segments
            if segment_count - last_progress_report >= 20:
                print(f"   📝 Processed {segment_count} segments...")
                last_progress_report = segment_count

        print(f"✅ Faster-Whisper produced {len(segments)} segments")
        
        # GUARANTEE: If no segments, create placeholder for monolog
        if not segments:
            print("   ⚠️ No segments from transcription. Creating placeholder...")
            # Try to get video duration for proper segmentation
            duration = self._get_video_duration_fallback()
            segments = self._create_placeholder_segments(duration)

        return {
            'language': getattr(info, 'language', language),
            'text': ' '.join(seg['text'] for seg in segments),
            'segments': segments
        }
    
    def _get_video_duration_fallback(self) -> float:
        """Get video duration using ffprobe"""
        import subprocess
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                self.video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except:
            return 60.0
    
    def _create_placeholder_segments(self, duration: float) -> List[Dict]:
        """Create placeholder segments when transcription fails"""
        segments = []
        segment_length = 10  # 10 second segments
        start = 0
        idx = 0
        
        while start < duration:
            end = min(start + segment_length, duration)
            segments.append({
                'id': idx,
                'start': start,
                'end': end,
                'text': f'Audio content {idx + 1}',
                'words': ['audio', 'content']
            })
            start = end
            idx += 1
        
        print(f"   📝 Created {len(segments)} placeholder segments")
        return segments
    
    def _transcribe_in_chunks_openai(self, language: str, chunk_duration: int = 300) -> Dict:
        """
        Fallback method: transcribe video in smaller chunks when timeout occurs.
        Splits video into chunks, processes separately, then merges results.
        """
        print(f"   🔄 Processing in {chunk_duration}s chunks...")
        duration = self._get_video_duration_fallback()
        
        all_segments = []
        segment_id = 0
        full_text = []
        
        # Process video in chunks
        import subprocess
        import tempfile
        import os
        
        num_chunks = int(duration / chunk_duration) + 1
        print(f"   📊 Total chunks to process: {num_chunks}")
        
        for chunk_idx in range(num_chunks):
            start_time = chunk_idx * chunk_duration
            if start_time >= duration:
                break
            
            chunk_end = min(start_time + chunk_duration, duration)
            actual_duration = chunk_end - start_time
            
            if actual_duration < 5:  # Skip very short chunks
                continue
            
            print(f"   🎬 Processing chunk {chunk_idx + 1}/{num_chunks} ({start_time:.0f}s - {chunk_end:.0f}s)...")
            
            try:
                # Extract chunk using FFmpeg
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                    chunk_path = temp_file.name
                
                ffmpeg_cmd = [
                    'ffmpeg', '-i', self.video_path,
                    '-ss', str(start_time),
                    '-t', str(actual_duration),
                    '-c', 'copy',
                    '-y', chunk_path
                ]
                subprocess.run(ffmpeg_cmd, capture_output=True, timeout=60)
                
                # Transcribe chunk
                chunk_result = self.model.transcribe(
                    chunk_path,
                    language=language,
                    task='transcribe',
                    verbose=False,
                    fp16=False
                )
                
                # Add offset to segment times
                for segment in chunk_result['segments']:
                    all_segments.append({
                        'id': segment_id,
                        'start': segment['start'] + start_time,
                        'end': segment['end'] + start_time,
                        'text': segment['text'].strip(),
                        'words': self._extract_words(segment['text'])
                    })
                    segment_id += 1
                
                full_text.append(chunk_result['text'])
                
                # Clean up temp file
                try:
                    os.unlink(chunk_path)
                except:
                    pass
                    
            except Exception as e:
                print(f"   ⚠️  Chunk {chunk_idx + 1} failed: {e}")
                # Create placeholder for failed chunk
                all_segments.append({
                    'id': segment_id,
                    'start': start_time,
                    'end': chunk_end,
                    'text': f'Audio content {chunk_idx + 1}',
                    'words': ['audio', 'content']
                })
                segment_id += 1
        
        print(f"   ✅ Chunk processing complete: {len(all_segments)} segments")
        
        return {
            'language': language,
            'text': ' '.join(full_text) if full_text else 'Transcription completed in chunks',
            'segments': all_segments
        }
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract clean words from text"""
        # Remove punctuation and convert to lowercase
        words = re.findall(r'\b\w+\b', text.lower())
        return words

    def _detect_meta_topic(self, text: str, words: List[str]) -> Tuple[str, float]:
        """Return the most relevant meta topic label and its strength (0-1)."""
        meta_topics = getattr(self.config, 'META_TOPICS', {})
        if not meta_topics:
            return 'Umum', 0.0
        best_label = 'Umum'
        best_score = 0.0
        for topic_id, data in meta_topics.items():
            keywords = data.get('keywords', [])
            if not keywords:
                continue
            single_tokens = [kw for kw in keywords if ' ' not in kw]
            phrase_tokens = [kw for kw in keywords if ' ' in kw]
            token_score = self._check_keywords(words, single_tokens)
            phrase_score = self._calculate_phrase_score(text, phrase_tokens)
            combined = max(token_score, phrase_score)
            if combined > best_score:
                best_score = combined
                best_label = data.get('label', topic_id)
        return best_label, min(1.0, best_score)

    def _calculate_phrase_score(self, text: str, phrases: List[str]) -> float:
        """Simple phrase matching score for multi-word keywords."""
        if not phrases:
            return 0.0
        lowered = text.lower()
        matches = sum(1 for phrase in phrases if phrase and phrase.lower() in lowered)
        return min(matches / 2.0, 1.0)
    
    def _analyze_content(self, transcript: Dict) -> Dict:
        """
        Analyze transcript content for viral potential
        GUARANTEED to return at least basic segment scores.
        """
        print("🧠 Analyzing content...")
        
        segments = transcript.get('segments', [])
        
        # Safety: If no segments, create placeholder
        if not segments:
            print("⚠️ No transcript segments! Creating placeholder...")
            segments = [{
                'id': 0,
                'start': 0,
                'end': 30,
                'text': 'Audio content',
                'words': ['audio', 'content']
            }]
        
        # Analyze each segment
        segment_scores = []
        for segment in segments:
            score = self._score_segment(segment)
            segment_scores.append({
                'segment_id': segment.get('id', len(segment_scores)),
                'start': segment.get('start', 0),
                'end': segment.get('end', segment.get('start', 0) + 5),
                'text': segment.get('text', ''),
                'scores': score
            })
        
        # Find hooks (strong opening statements)
        hooks = self._find_hooks(segments)
        
        # Find punchlines (impactful statements)
        punchlines = self._find_punchlines(segments)
        
        # Overall content analysis
        overall = self._calculate_overall_scores(segment_scores)
        
        print(f"📊 Analyzed {len(segment_scores)} segments")
        
        return {
            'segment_scores': segment_scores,
            'hooks': hooks,
            'punchlines': punchlines,
            'overall': overall
        }
    
    def _score_segment(self, segment: Dict) -> Dict:
        """
        Score a single segment for various qualities
        Enhanced with money/urgency, meta topics, and relatability detection
        Returns default scores if segment is empty.
        """
        raw_text = segment.get('text') or ''
        text = raw_text.lower()
        words = segment.get('words', [])
        
        # If no words, extract from text
        if not words and raw_text:
            words = self._extract_words(raw_text)
        
        # Check for viral keywords (including new categories)
        hook_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS.get('hook', []))
        emotional_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS.get('emotional', []))
        controversial_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS.get('controversial', []))
        educational_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS.get('educational', []))
        entertaining_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS.get('entertaining', []))
        
        # NEW: Check for money and urgency keywords
        money_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS.get('money', []))
        urgency_score = self._check_keywords(words, self.config.VIRAL_KEYWORDS.get('urgency', []))
        
        # Check for filler words (negative score) - reduced penalty
        filler_count = sum(1 for word in words if word in self.config.FILLER_WORDS)
        filler_penalty = min(filler_count * 0.08, 0.4)  # Reduced from 0.1 and 0.5
        
        # Check for questions (engaging)
        has_question = '?' in segment['text']
        question_bonus = 0.2 if has_question else 0
        
        # Check for numbers/stats (credibility)
        has_numbers = bool(re.search(r'\d+', segment['text']))
        numbers_bonus = 0.15 if has_numbers else 0
        
        # Check for exclamation marks (emphasis)
        has_exclamation = '!' in segment['text']
        emphasis_bonus = 0.1 if has_exclamation else 0
        
        # Meta topic / mental slap detection
        meta_topic_label, meta_topic_strength = self._detect_meta_topic(raw_text, words)
        mental_slap_score = self._check_keywords(
            words,
            getattr(self.config, 'MENTAL_SLAP_KEYWORDS', [])
        )
        rare_topic_score = self._check_keywords(
            words,
            getattr(self.config, 'RARE_TOPICS', [])
        )

        # Enhanced engagement calculation with money, urgency, and relatability
        engagement = (
            hook_score * 0.25 +
            emotional_score * 0.18 +  # Slightly reduced
            controversial_score * 0.12 +  # Slightly reduced
            educational_score * 0.12 +  # Slightly reduced
            entertaining_score * 0.12 +  # Slightly reduced
            money_score * 0.15 +  # NEW: Money keywords are highly engaging
            urgency_score * 0.15 +  # NEW: Urgency creates FOMO
            meta_topic_strength * 0.12 +
            mental_slap_score * 0.18 +
            question_bonus +
            numbers_bonus +
            emphasis_bonus -
            filler_penalty -
            rare_topic_score * 0.2
        )
        
        engagement = max(0, min(1, engagement))  # Clamp to 0-1
        
        return {
            'hook': hook_score,
            'emotional': emotional_score,
            'controversial': controversial_score,
            'educational': educational_score,
            'entertaining': entertaining_score,
            'money': money_score,
            'urgency': urgency_score,
            'meta_topic': meta_topic_label,
            'meta_topic_strength': meta_topic_strength,
            'mental_slap': mental_slap_score,
            'rare_topic': rare_topic_score,
            'engagement': engagement,
            'has_question': has_question,
            'has_numbers': has_numbers,
            'has_exclamation': has_exclamation,
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
