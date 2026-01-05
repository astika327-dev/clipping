"""
Audio Analyzer Module
Handles audio transcription and content analysis using Whisper
Enhanced with Hybrid Transcription System for improved accuracy
"""
import re
import os
import json
import tempfile
import subprocess
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

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

try:
    import httpx
except ImportError:  # pragma: no cover - optional for Groq API
    httpx = None

class AudioAnalyzer:
    def __init__(self, video_path: str, config, overrides: Optional[Dict[str, str]] = None):
        self.video_path = video_path
        self.config = config
        self.model = None
        self.transcript = None
        self.faster_model = None
        self.retry_model = None  # For confidence-based retry
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
        
        # === HYBRID TRANSCRIPTION SETTINGS ===
        self.hybrid_enabled = getattr(config, 'HYBRID_TRANSCRIPTION_ENABLED', True)
        self.confidence_threshold = getattr(config, 'CONFIDENCE_RETRY_THRESHOLD', 0.7)
        self.retry_model_name = getattr(config, 'RETRY_MODEL', 'large-v3')
        self.retry_beam_size = getattr(config, 'RETRY_BEAM_SIZE', 5)
        
        # Dual-model comparison settings
        self.dual_model_enabled = getattr(config, 'DUAL_MODEL_ENABLED', True)
        self.dual_model_max_duration = getattr(config, 'DUAL_MODEL_MAX_DURATION', 600)
        self.dual_model_secondary = getattr(config, 'DUAL_MODEL_SECONDARY', 'large-v3-turbo')
        
        # Groq API settings
        self.groq_enabled = getattr(config, 'GROQ_API_ENABLED', True)
        self.groq_api_key = getattr(config, 'GROQ_API_KEY', '')
        self.groq_model = getattr(config, 'GROQ_MODEL', 'whisper-large-v3-turbo')
        self.groq_fallback_on_low_confidence = getattr(config, 'GROQ_FALLBACK_ON_LOW_CONFIDENCE', True)
        self.groq_confidence_threshold = getattr(config, 'GROQ_CONFIDENCE_THRESHOLD', 0.6)
        self.min_segment_confidence = getattr(config, 'MIN_SEGMENT_CONFIDENCE', 0.5)
        
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

        # Cleanup: Unload models to free memory
        self._cleanup_models()
        
        return {
            'transcript': transcript,
            'analysis': content_analysis
        }
    
    def _cleanup_models(self):
        """Unload Whisper models to free memory after transcription."""
        import gc
        
        freed_memory = False
        
        if self.model is not None:
            print("   🧹 Unloading openai-whisper model...")
            del self.model
            self.model = None
            freed_memory = True
        
        if self.faster_model is not None:
            print("   🧹 Unloading faster-whisper model...")
            del self.faster_model
            self.faster_model = None
            freed_memory = True
        
        if self.retry_model is not None:
            print("   🧹 Unloading retry model...")
            del self.retry_model
            self.retry_model = None
            freed_memory = True
        
        if freed_memory:
            # Force garbage collection
            gc.collect()
            
            # Clear CUDA cache if available
            if torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("   🧹 CUDA cache cleared")
            
            print("   ✅ Model memory freed")
    
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
        - Confidence tracking for hybrid transcription
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
        low_confidence_segments = []
        segment_count = 0
        last_progress_report = 0
        total_confidence = 0.0
        
        for idx, segment in enumerate(segments_iter):
            text = segment.text.strip()
            if not text:  # Skip empty segments
                continue
            
            # Calculate confidence from avg_logprob (typical range: -1.0 to 0.0)
            # Convert to 0-1 scale where higher is better
            avg_logprob = getattr(segment, 'avg_logprob', -0.5)
            no_speech_prob = getattr(segment, 'no_speech_prob', 0.0)
            
            # Confidence formula: higher logprob = higher confidence, penalize no_speech
            confidence = min(1.0, max(0.0, (avg_logprob + 1.0) * (1.0 - no_speech_prob)))
            total_confidence += confidence
            
            seg_data = {
                'id': idx,
                'start': segment.start,
                'end': segment.end,
                'text': text,
                'words': self._extract_words(text),
                'confidence': confidence,
                'avg_logprob': avg_logprob,
                'no_speech_prob': no_speech_prob
            }
            segments.append(seg_data)
            segment_count += 1
            
            # Track low confidence segments for retry
            if confidence < self.confidence_threshold:
                low_confidence_segments.append(seg_data)
            
            # Progress reporting every 20 segments
            if segment_count - last_progress_report >= 20:
                print(f"   📝 Processed {segment_count} segments...")
                last_progress_report = segment_count

        avg_confidence = total_confidence / len(segments) if segments else 0.0
        print(f"✅ Faster-Whisper produced {len(segments)} segments (avg confidence: {avg_confidence:.2f})")
        
        # Track low confidence segments for hybrid processing
        if low_confidence_segments:
            print(f"   ⚠️ Found {len(low_confidence_segments)} low-confidence segments (< {self.confidence_threshold})")
        
        # GUARANTEE: If no segments, create placeholder for monolog
        if not segments:
            print("   ⚠️ No segments from transcription. Creating placeholder...")
            # Try to get video duration for proper segmentation
            duration = self._get_video_duration_fallback()
            segments = self._create_placeholder_segments(duration)
            avg_confidence = 0.0
            low_confidence_segments = segments.copy()

        result = {
            'language': getattr(info, 'language', language),
            'text': ' '.join(seg['text'] for seg in segments),
            'segments': segments,
            'avg_confidence': avg_confidence,
            'low_confidence_segments': low_confidence_segments
        }
        
        # === HYBRID TRANSCRIPTION PROCESSING ===
        if self.hybrid_enabled and low_confidence_segments:
            result = self._process_hybrid_transcription(result, language)
        
        return result
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
    
    # === HYBRID TRANSCRIPTION METHODS ===
    
    def _process_hybrid_transcription(self, result: Dict, language: str) -> Dict:
        """
        Orchestrate hybrid transcription processing:
        1. Retry low-confidence segments with larger model
        2. Use Groq API for stubborn segments
        3. Merge improved segments back into result
        """
        low_confidence_segments = result.get('low_confidence_segments', [])
        if not low_confidence_segments:
            return result
        
        print(f"\n🔄 HYBRID TRANSCRIPTION: Processing {len(low_confidence_segments)} low-confidence segments...")
        
        improved_segments = {}
        still_low_confidence = []
        
        # Step 1: Retry with larger model
        print(f"   📈 Step 1: Retrying with larger model ({self.retry_model_name})...")
        for seg in low_confidence_segments:
            try:
                improved = self._retry_with_larger_model(seg, language)
                if improved and improved.get('confidence', 0) > seg.get('confidence', 0):
                    improved_segments[seg['id']] = improved
                    print(f"      ✅ Segment {seg['id']}: {seg.get('confidence', 0):.2f} → {improved.get('confidence', 0):.2f}")
                else:
                    still_low_confidence.append(seg)
            except Exception as e:
                print(f"      ❌ Segment {seg['id']} retry failed: {e}")
                still_low_confidence.append(seg)
        
        # Step 2: Use Groq API for remaining low confidence segments
        if still_low_confidence and self.groq_enabled and self.groq_api_key:
            print(f"   🌐 Step 2: Using Groq API for {len(still_low_confidence)} remaining segments...")
            for seg in still_low_confidence:
                try:
                    groq_result = self._transcribe_with_groq(seg, language)
                    if groq_result and groq_result.get('text'):
                        improved_segments[seg['id']] = groq_result
                        print(f"      ✅ Segment {seg['id']}: Groq API success")
                except Exception as e:
                    print(f"      ⚠️ Segment {seg['id']} Groq failed: {e}")
        elif still_low_confidence:
            if not self.groq_api_key:
                print(f"   ⚠️ Groq API key not set. Set GROQ_API_KEY env variable for better accuracy.")
            print(f"   ℹ️  {len(still_low_confidence)} segments remain at low confidence")
        
        # Step 3: Merge improved segments back into result
        if improved_segments:
            print(f"   🔗 Merging {len(improved_segments)} improved segments...")
            new_segments = []
            for seg in result['segments']:
                if seg['id'] in improved_segments:
                    improved = improved_segments[seg['id']]
                    # Preserve original timing, update text and confidence
                    seg['text'] = improved.get('text', seg['text'])
                    seg['words'] = self._extract_words(seg['text'])
                    seg['confidence'] = improved.get('confidence', seg.get('confidence', 0))
                    seg['improved_by'] = improved.get('source', 'retry')
                new_segments.append(seg)
            
            result['segments'] = new_segments
            result['text'] = ' '.join(seg['text'] for seg in new_segments)
            
            # Recalculate average confidence
            total_conf = sum(seg.get('confidence', 0) for seg in new_segments)
            result['avg_confidence'] = total_conf / len(new_segments) if new_segments else 0
            result['hybrid_improvements'] = len(improved_segments)
            
            print(f"   ✅ Hybrid processing complete! New avg confidence: {result['avg_confidence']:.2f}")
        
        return result
    
    def _retry_with_larger_model(self, segment: Dict, language: str) -> Optional[Dict]:
        """
        Retry transcribing a specific segment with a larger, more accurate model.
        Extracts just the audio for that segment and re-transcribes.
        """
        if FasterWhisperModel is None:
            return None
        
        start_time = segment.get('start', 0)
        end_time = segment.get('end', start_time + 5)
        duration = end_time - start_time
        
        # Skip very short segments
        if duration < 1.0:
            return None
        
        # Extract audio segment
        audio_path = self._extract_audio_segment(start_time, end_time)
        if not audio_path:
            return None
        
        try:
            # Load retry model lazily
            if self.retry_model is None:
                print(f"      📥 Loading retry model: {self.retry_model_name}")
                self.retry_model = FasterWhisperModel(
                    self.retry_model_name,
                    device=self.faster_device,
                    compute_type=self.faster_compute_type
                )
            
            # Transcribe with higher accuracy settings
            segments_iter, info = self.retry_model.transcribe(
                audio_path,
                language=language,
                beam_size=self.retry_beam_size,  # Higher beam for accuracy
                word_timestamps=False,
                vad_filter=False,  # Process all audio
                temperature=0.0  # More deterministic
            )
            
            # Collect all text from the segment
            texts = []
            total_logprob = 0
            count = 0
            
            for seg in segments_iter:
                text = seg.text.strip()
                if text:
                    texts.append(text)
                    total_logprob += getattr(seg, 'avg_logprob', -0.5)
                    count += 1
            
            if texts:
                avg_logprob = total_logprob / count if count > 0 else -0.5
                confidence = min(1.0, max(0.0, (avg_logprob + 1.0)))
                
                return {
                    'text': ' '.join(texts),
                    'confidence': confidence,
                    'source': 'retry_model'
                }
        except Exception as e:
            print(f"      ⚠️ Retry model error: {e}")
        finally:
            # Cleanup temp file
            try:
                if audio_path and os.path.exists(audio_path):
                    os.unlink(audio_path)
            except:
                pass
        
        return None
    
    def _transcribe_with_groq(self, segment: Dict, language: str) -> Optional[Dict]:
        """
        Use Groq API to transcribe a specific segment.
        Groq offers free tier with fast Whisper inference.
        """
        if httpx is None:
            print("      ⚠️ httpx not installed. Install with: pip install httpx")
            return None
        
        if not self.groq_api_key:
            return None
        
        start_time = segment.get('start', 0)
        end_time = segment.get('end', start_time + 5)
        
        # Extract audio segment as file
        audio_path = self._extract_audio_segment(start_time, end_time, format='mp3')
        if not audio_path:
            return None
        
        try:
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # Call Groq API
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}"
            }
            
            files = {
                'file': ('audio.mp3', audio_data, 'audio/mpeg'),
                'model': (None, self.groq_model),
                'language': (None, language),
                'response_format': (None, 'verbose_json')
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, files=files)
                response.raise_for_status()
                result = response.json()
            
            text = result.get('text', '').strip()
            if text:
                # Groq doesn't provide confidence, estimate from response
                return {
                    'text': text,
                    'confidence': 0.85,  # Assume good confidence from Groq
                    'source': 'groq_api'
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print("      ❌ Groq API: Invalid API key")
            elif e.response.status_code == 429:
                print("      ⚠️ Groq API: Rate limit exceeded")
            else:
                print(f"      ❌ Groq API error: {e.response.status_code}")
        except Exception as e:
            print(f"      ❌ Groq API error: {e}")
        finally:
            # Cleanup temp file
            try:
                if audio_path and os.path.exists(audio_path):
                    os.unlink(audio_path)
            except:
                pass
        
        return None
    
    def _extract_audio_segment(self, start: float, end: float, format: str = 'wav') -> Optional[str]:
        """
        Extract a specific audio segment from the video using FFmpeg.
        Returns path to temporary audio file.
        """
        try:
            duration = end - start
            
            # Create temp file
            suffix = f'.{format}'
            fd, temp_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            
            # FFmpeg command to extract audio segment
            cmd = [
                'ffmpeg', '-y',
                '-i', self.video_path,
                '-ss', str(start),
                '-t', str(duration),
                '-vn',  # No video
                '-acodec', 'pcm_s16le' if format == 'wav' else 'libmp3lame',
                '-ar', '16000',  # 16kHz for speech
                '-ac', '1',  # Mono
                temp_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(temp_path):
                return temp_path
            else:
                print(f"      ⚠️ FFmpeg extraction failed: {result.stderr.decode()[:100]}")
                return None
        except Exception as e:
            print(f"      ⚠️ Audio extraction error: {e}")
            return None
    
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
        """Extract normalized tokens from text."""
        return self._tokenize(text)

    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword/phrase matching."""
        if not text:
            return ''
        lowered = text.lower()
        normalized = re.sub(r'[^a-z0-9\s]', ' ', lowered)
        return re.sub(r'\s+', ' ', normalized).strip()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize normalized text into words."""
        normalized = self._normalize_text(text)
        return [tok for tok in normalized.split() if tok]

    def _simple_stem(self, token: str) -> str:
        """
        Lightweight stemming for Indonesian/English without external deps.
        Keeps it conservative to avoid over-stemming.
        """
        if not token or len(token) <= 3:
            return token

        # Common Indonesian enclitics
        for suffix in ('lah', 'kah', 'tah', 'pun', 'nya', 'ku', 'mu'):
            if token.endswith(suffix) and len(token) > len(suffix) + 2:
                token = token[: -len(suffix)]
                break

        # Indonesian derivational suffixes
        for suffix in ('kan', 'an', 'i'):
            if token.endswith(suffix) and len(token) > len(suffix) + 3:
                token = token[: -len(suffix)]
                break

        # Simple English suffixes
        for suffix in ('ing', 'ed', 'es', 's'):
            if token.endswith(suffix) and len(token) > len(suffix) + 3:
                token = token[: -len(suffix)]
                break

        return token

    def _stem_tokens(self, tokens: List[str]) -> List[str]:
        return [self._simple_stem(tok) for tok in tokens]

    def _split_keywords(self, keywords: List[str]) -> Tuple[List[str], List[str]]:
        """Separate single-token keywords from multi-word phrases."""
        tokens = []
        phrases = []
        for kw in keywords or []:
            if not kw:
                continue
            if ' ' in kw.strip():
                phrases.append(kw.strip().lower())
            else:
                tokens.append(kw.strip().lower())
        return tokens, phrases

    def _count_phrase_matches(self, stemmed_text: str, phrases: List[str]) -> int:
        if not stemmed_text or not phrases:
            return 0
        matches = 0
        for phrase in phrases:
            phrase_tokens = [self._simple_stem(tok) for tok in phrase.split()]
            if not phrase_tokens:
                continue
            pattern = r'\b' + r'\s+'.join(map(re.escape, phrase_tokens)) + r'\b'
            found = re.findall(pattern, stemmed_text)
            matches += len(found)
        return matches

    def _keyword_scores(self, text: str, tokens: List[str], keywords: List[str]) -> Dict[str, float]:
        """
        Compute separate token and phrase scores to avoid bias.
        Returns token_score, phrase_score, combined.
        """
        token_keywords, phrase_keywords = self._split_keywords(keywords)
        stemmed_tokens = self._stem_tokens(tokens)
        stemmed_text = ' '.join(stemmed_tokens)

        token_matches = sum(1 for tok in stemmed_tokens if tok in token_keywords)
        phrase_matches = self._count_phrase_matches(stemmed_text, phrase_keywords)

        token_score = min(token_matches / 3.0, 1.0)
        phrase_score = min(phrase_matches / 2.0, 1.0)

        # Probabilistic OR to prevent stacking bias
        combined = 1 - ((1 - token_score) * (1 - phrase_score))

        return {
            'token_score': token_score,
            'phrase_score': phrase_score,
            'combined': combined,
            'token_matches': token_matches,
            'phrase_matches': phrase_matches
        }

    def _detect_meta_topic(self, text: str, words: List[str]) -> Tuple[str, float]:
        """Return the most relevant meta topic label and its strength (0-1)."""
        meta_topics = getattr(self.config, 'META_TOPICS', {})
        if not meta_topics:
            return 'Umum', 0.0
        best_label = 'Umum'
        best_score = 0.0
        normalized_text = self._normalize_text(text)
        tokens = words or self._tokenize(normalized_text)
        for topic_id, data in meta_topics.items():
            keywords = data.get('keywords', [])
            if not keywords:
                continue
            scores = self._keyword_scores(normalized_text, tokens, keywords)
            combined = scores['combined']
            if combined > best_score:
                best_score = combined
                best_label = data.get('label', topic_id)
        return best_label, min(1.0, best_score)

    def _calculate_phrase_score(self, text: str, phrases: List[str]) -> float:
        """Simple phrase matching score for multi-word keywords."""
        if not phrases:
            return 0.0
        normalized = self._normalize_text(text)
        stemmed = ' '.join(self._stem_tokens(normalized.split()))
        matches = self._count_phrase_matches(stemmed, phrases)
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
        normalized_text = self._normalize_text(raw_text)
        tokens = self._tokenize(normalized_text)

        # Check for viral keywords (token vs phrase separated)
        hook_scores = self._keyword_scores(normalized_text, tokens, self.config.VIRAL_KEYWORDS.get('hook', []))
        emotional_scores = self._keyword_scores(normalized_text, tokens, self.config.VIRAL_KEYWORDS.get('emotional', []))
        controversial_scores = self._keyword_scores(normalized_text, tokens, self.config.VIRAL_KEYWORDS.get('controversial', []))
        educational_scores = self._keyword_scores(normalized_text, tokens, self.config.VIRAL_KEYWORDS.get('educational', []))
        entertaining_scores = self._keyword_scores(normalized_text, tokens, self.config.VIRAL_KEYWORDS.get('entertaining', []))
        money_scores = self._keyword_scores(normalized_text, tokens, self.config.VIRAL_KEYWORDS.get('money', []))
        urgency_scores = self._keyword_scores(normalized_text, tokens, self.config.VIRAL_KEYWORDS.get('urgency', []))

        hook_score = hook_scores['combined']
        emotional_score = emotional_scores['combined']
        controversial_score = controversial_scores['combined']
        educational_score = educational_scores['combined']
        entertaining_score = entertaining_scores['combined']
        money_score = money_scores['combined']
        urgency_score = urgency_scores['combined']

        # Check for filler words (negative score) - reduce bias for phrases
        filler_tokens, filler_phrases = self._split_keywords(self.config.FILLER_WORDS)
        stemmed_text = ' '.join(self._stem_tokens(tokens))
        filler_token_matches = sum(1 for tok in self._stem_tokens(tokens) if tok in filler_tokens)
        filler_phrase_matches = self._count_phrase_matches(stemmed_text, filler_phrases)
        filler_count = filler_token_matches + (filler_phrase_matches * 2)
        filler_penalty = min(filler_count * 0.08, 0.4)
        
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
        meta_topic_label, meta_topic_strength = self._detect_meta_topic(raw_text, tokens)
        mental_slap_score = self._keyword_scores(
            normalized_text,
            tokens,
            getattr(self.config, 'MENTAL_SLAP_KEYWORDS', [])
        )['combined']
        rare_topic_score = self._keyword_scores(
            normalized_text,
            tokens,
            getattr(self.config, 'RARE_TOPICS', [])
        )['combined']

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
            'hook_token': hook_scores['token_score'],
            'hook_phrase': hook_scores['phrase_score'],
            'emotional_token': emotional_scores['token_score'],
            'emotional_phrase': emotional_scores['phrase_score'],
            'controversial_token': controversial_scores['token_score'],
            'controversial_phrase': controversial_scores['phrase_score'],
            'educational_token': educational_scores['token_score'],
            'educational_phrase': educational_scores['phrase_score'],
            'entertaining_token': entertaining_scores['token_score'],
            'entertaining_phrase': entertaining_scores['phrase_score'],
            'money_token': money_scores['token_score'],
            'money_phrase': money_scores['phrase_score'],
            'urgency_token': urgency_scores['token_score'],
            'urgency_phrase': urgency_scores['phrase_score'],
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
        Backwards-compatible keyword score (token-only).
        Prefer _keyword_scores() for new logic.
        """
        matches = sum(1 for word in words if word in (keywords or []))
        return min(matches / 3.0, 1.0)
    
    def _find_hooks(self, segments: List[Dict]) -> List[Dict]:
        """
        Find potential hooks (strong opening statements)
        Usually in first 10 seconds or after scene changes
        """
        hooks = []
        
        for segment in segments[:5]:  # Check first 5 segments
            text = segment.get('text', '')
            tokens = self._tokenize(text)
            hook_score = self._keyword_scores(
                text, tokens, self.config.VIRAL_KEYWORDS['hook']
            )['combined']
            
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
            text = segment.get('text', '')
            tokens = self._tokenize(text)
            
            # Punchlines often have:
            # - Emotional words
            # - Controversial statements
            # - Surprising facts
            # - Strong opinions
            
            emotional = self._keyword_scores(
                text, tokens, self.config.VIRAL_KEYWORDS['emotional']
            )['combined']
            controversial = self._keyword_scores(
                text, tokens, self.config.VIRAL_KEYWORDS['controversial']
            )['combined']
            
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
