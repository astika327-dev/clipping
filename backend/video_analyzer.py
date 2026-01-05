"""
Video Analyzer Module - OPTIMIZED VERSION
Handles video analysis including scene detection, face detection, and visual analysis
Optimized for long monolog/podcast videos with minimal scene changes
"""
import cv2
import numpy as np
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
import os
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading

class VideoAnalyzer:
    def __init__(self, video_path: str, config):
        self.video_path = video_path
        self.config = config
        self.scenes = []
        self._face_cascade = None  # Lazy load
        self._analysis_cache = {}
        self._lock = threading.Lock()
        
    @property
    def face_cascade(self):
        """Lazy load face cascade to reduce startup time"""
        if self._face_cascade is None:
            self._face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        return self._face_cascade
        
    def analyze(self) -> Dict:
        """
        Main analysis function - OPTIMIZED
        Returns comprehensive video analysis
        GUARANTEED to return valid structure even if analysis fails.
        Optimized for monolog/podcast videos.
        """
        print(f"🎬 Analyzing video: {self.video_path}")
        
        try:
            # Get video metadata first (fast)
            metadata = self._get_video_metadata()
            duration = metadata.get('duration', 0)
            
            print(f"   📊 Video duration: {duration:.1f}s, Resolution: {metadata.get('width')}x{metadata.get('height')}")
            
            # Detect scenes with optimization
            scenes = self._detect_scenes_optimized(duration)
            
            # IMPROVED MONOLOG DETECTION
            # Calculate scene density (scenes per minute)
            scenes_per_minute = len(scenes) / (duration / 60) if duration > 0 else 0
            is_long_form = duration > 180  # > 3 minutes
            
            # Multiple conditions for monolog detection:
            # 1. Very low scene density (< 0.5 scenes/min)
            # 2. Long video with few scenes
            # 3. Very long video with relatively few scenes
            is_monolog = (
                (scenes_per_minute < 0.5) or  # Less than 0.5 scenes per minute
                (is_long_form and len(scenes) < 10) or  # >3min with <10 scenes
                (duration > 600 and len(scenes) < 15) or  # >10min with <15 scenes
                (duration > 1800 and len(scenes) < 25)  # >30min with <25 scenes
            )
            
            # For monolog/podcast: create time-based pseudo-scenes for better clip variety
            if is_monolog and duration > 30:
                print(f"   📺 Monolog/podcast detected ({scenes_per_minute:.2f} scenes/min, {len(scenes)} scenes total)")
                print(f"      Creating synthetic segments for better clip coverage...")
                scenes = self._create_monolog_scenes(duration, existing_scenes=scenes)
            
            # Analyze scenes with sampling optimization
            scene_analysis = self._analyze_scenes_optimized(scenes, metadata)
            visual_windows = self._build_visual_windows(scene_analysis, duration)
            
            return {
                'metadata': metadata,
                'scenes': scene_analysis,
                'visual_windows': visual_windows,
                'total_scenes': len(scene_analysis),
                'duration': duration,
                'is_monolog': is_monolog,  # Enhanced flag for downstream processing
                'scenes_per_minute': scenes_per_minute  # Added for debugging
            }
        except Exception as e:
            print(f"⚠️ Video analysis error: {e}")
            print("   Returning fallback analysis with synthetic scenes...")
            
            # Return minimal valid structure WITH synthetic scenes for monolog
            duration = self._get_video_duration_fallback()
            synthetic_scenes = self._create_monolog_scenes(duration)
            
            return {
                'metadata': {
                    'fps': 30,
                    'frame_count': int(duration * 30),
                    'width': 1920,
                    'height': 1080,
                    'duration': duration,
                    'aspect_ratio': '1920:1080'
                },
                'scenes': synthetic_scenes,
                'visual_windows': self._build_visual_windows(synthetic_scenes, duration),
                'total_scenes': len(synthetic_scenes),
                'duration': duration,
                'is_monolog': True
            }
    
    def _get_video_duration_fallback(self) -> float:
        """Get video duration using FFprobe as fallback."""
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
            return 60.0  # Default 60 seconds
    
    def _get_video_metadata(self) -> Dict:
        """Get basic video information - cached"""
        cache_key = 'metadata'
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]
            
        cap = cv2.VideoCapture(self.video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        metadata = {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': duration,
            'aspect_ratio': f"{width}:{height}"
        }
        
        self._analysis_cache[cache_key] = metadata
        return metadata
    
    def _detect_scenes_optimized(self, duration: float) -> List[Tuple[float, float]]:
        """
        Detect scene changes in video - OPTIMIZED VERSION
        Uses frame skipping for long videos
        Returns list of (start_time, end_time) tuples
        """
        print("🔍 Detecting scenes (optimized)...")
        
        try:
            # For very long videos (>10 min), use more aggressive detection
            threshold = self.config.SCENE_THRESHOLD
            if duration > 600:  # > 10 minutes
                threshold = max(threshold - 5, 10)  # Lower threshold for better detection
                print(f"   Long video detected. Using threshold: {threshold}")
            
            video_manager = VideoManager([self.video_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(
                ContentDetector(threshold=threshold)
            )
            
            # Start video manager
            video_manager.start()
            
            # Detect scenes
            scene_manager.detect_scenes(video_manager)
            
            # Get scene list
            scene_list = scene_manager.get_scene_list()
            
            # Convert to seconds
            scenes = []
            for scene in scene_list:
                start_time = scene[0].get_seconds()
                end_time = scene[1].get_seconds()
                
                # Filter by minimum scene length
                if end_time - start_time >= self.config.MIN_SCENE_LENGTH:
                    scenes.append((start_time, end_time))
            
            video_manager.release()
            
            print(f"✅ Found {len(scenes)} scenes")
            return scenes
            
        except Exception as e:
            print(f"⚠️ Scene detection failed: {e}")
            return []
    
    def _create_monolog_scenes(self, duration: float, existing_scenes: List[Tuple[float, float]] = None) -> List[Dict]:
        """
        Create synthetic scenes for monolog/podcast videos.
        Ensures we always have segments to work with.
        ENHANCED: Better segment lengths for long podcasts (1-2+ hours).
        """
        if existing_scenes is None:
            existing_scenes = []
            
        # Calculate optimal segment lengths based on duration
        # Longer videos need longer segments for context
        if duration <= 60:
            segment_lengths = [15, 20]
        elif duration <= 300:  # 5 minutes
            segment_lengths = [15, 20, 25]
        elif duration <= 1800:  # 30 minutes
            segment_lengths = [20, 25, 30, 40]
        elif duration <= 3600:  # 1 hour
            segment_lengths = [25, 30, 40, 50]  # Longer segments for podcasts
        else:  # > 1 hour (very long podcasts)
            segment_lengths = [30, 40, 50, 60]  # Even longer for epic conversations
        
        synthetic_scenes = []
        
        # Create overlapping segments at different lengths for variety
        for seg_length in segment_lengths:
            step = seg_length * 0.6  # 60% overlap
            start = 0
            
            while start + seg_length <= duration + 5:
                end = min(start + seg_length, duration)
                
                # Skip if this overlaps too much with existing detected scenes
                skip = False
                for existing_start, existing_end in existing_scenes:
                    overlap = min(end, existing_end) - max(start, existing_start)
                    if overlap > seg_length * 0.7:
                        skip = True
                        break
                
                if not skip and end - start >= 8:
                    synthetic_scenes.append({
                        'scene_id': len(synthetic_scenes),
                        'start_time': start,
                        'end_time': end,
                        'duration': end - start,
                        'has_faces': True,  # Assume talking head for monolog
                        'face_count': 1.0,
                        'has_closeup': True,
                        'motion_score': 15.0,  # Low motion typical for monolog
                        'has_high_motion': False,
                        'brightness': 128.0,
                        'visual_engagement': 0.55,  # Moderate engagement
                        'is_synthetic': True
                    })
                
                start += step
        
        # Also add the existing detected scenes
        for idx, (start_time, end_time) in enumerate(existing_scenes):
            synthetic_scenes.append({
                'scene_id': len(synthetic_scenes),
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'has_faces': True,
                'face_count': 1.0,
                'has_closeup': True,
                'motion_score': 20.0,
                'has_high_motion': False,
                'brightness': 128.0,
                'visual_engagement': 0.6,
                'is_synthetic': False
            })
        
        # Sort by start time
        synthetic_scenes.sort(key=lambda x: x['start_time'])
        
        print(f"   📺 Created {len(synthetic_scenes)} segments for monolog processing")
        return synthetic_scenes
    
    def _analyze_scenes_optimized(self, scenes: List, metadata: Dict) -> List[Dict]:
        """
        Analyze scenes with optimizations:
        - Reduced frame sampling for long videos
        - Skip face detection for already-analyzed synthetic scenes
        - Parallel processing hints
        """
        # If scenes are already fully analyzed (synthetic), return as-is
        if scenes and isinstance(scenes[0], dict):
            return scenes
            
        print("🎭 Analyzing scene content (optimized)...")
        
        cap = cv2.VideoCapture(self.video_path)
        fps = metadata.get('fps', 30)
        duration = metadata.get('duration', 0)
        
        scene_analysis = []
        total_scenes = len(scenes)
        
        # Determine sampling rate based on video length
        # For long videos, analyze fewer frames per scene
        if duration > 600:  # > 10 minutes
            samples_per_scene = 3
        elif duration > 300:  # > 5 minutes
            samples_per_scene = 4
        else:
            samples_per_scene = 5
        
        # For very many scenes, analyze only a subset
        # IMPROVED: Filter out very short scenes and prefer longer ones
        max_scenes_to_analyze = min(total_scenes, 50)
        
        if total_scenes > max_scenes_to_analyze:
            print(f"   ⚡ Many scenes ({total_scenes}). Filtering and sampling for analysis...")
            
            # First, filter to only scenes >= 5 seconds (meaningful for clips)
            valid_scenes = [s for s in scenes if (
                (s[1] - s[0] if isinstance(s, tuple) else s['end_time'] - s['start_time']) >= 5.0
            )]
            
            if len(valid_scenes) < 10:
                # Not enough long scenes, use all
                valid_scenes = scenes
            
            # Sample evenly across the video from valid scenes
            step = max(1, len(valid_scenes) // max_scenes_to_analyze)
            scenes_to_analyze = valid_scenes[::step][:max_scenes_to_analyze]
            
            print(f"   📊 Selected {len(scenes_to_analyze)} meaningful scenes (filtered {total_scenes - len(valid_scenes)} short scenes)")
        else:
            scenes_to_analyze = scenes
        
        for idx, scene_data in enumerate(scenes_to_analyze):
            # Handle both tuple format and dict format
            if isinstance(scene_data, tuple):
                start_time, end_time = scene_data
            else:
                start_time = scene_data['start_time']
                end_time = scene_data['end_time']
            
            if idx % 10 == 0 or idx == len(scenes_to_analyze) - 1:
                print(f"  Scene {idx + 1}/{len(scenes_to_analyze)}: {start_time:.2f}s - {end_time:.2f}s")
            
            # Sample frames from this scene
            analysis = self._analyze_scene_segment_fast(cap, start_time, end_time, fps, samples_per_scene)
            
            scene_analysis.append({
                'scene_id': idx,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                **analysis
            })
        
        cap.release()
        
        return scene_analysis

    def _build_visual_windows(self, scenes: List[Dict], duration: float) -> List[Dict]:
        """
        Build coarse visual windows for audio-first merging.
        Windows are lightweight summaries (no extra video decoding).
        """
        if not scenes or duration <= 0:
            return []

        window_seconds = float(getattr(self.config, 'VISUAL_WINDOW_SECONDS', 10))
        step_ratio = float(getattr(self.config, 'VISUAL_WINDOW_STEP_RATIO', 0.5))
        step = max(1.0, window_seconds * step_ratio)

        windows = []
        start = 0.0
        while start < duration:
            end = min(start + window_seconds, duration)
            overlap_total = 0.0
            sums = {
                'face_count': 0.0,
                'motion_score': 0.0,
                'visual_engagement': 0.0,
            }
            bool_sums = {
                'has_faces': 0.0,
                'has_closeup': 0.0,
                'has_high_motion': 0.0,
                'is_talking': 0.0,
            }
            for scene in scenes:
                overlap = min(end, scene.get('end_time', 0)) - max(start, scene.get('start_time', 0))
                if overlap <= 0:
                    continue
                overlap_total += overlap
                sums['face_count'] += scene.get('face_count', 1) * overlap
                sums['motion_score'] += scene.get('motion_score', 0.3) * overlap
                sums['visual_engagement'] += scene.get('visual_engagement', 0.5) * overlap
                bool_sums['has_faces'] += float(bool(scene.get('has_faces', True))) * overlap
                bool_sums['has_closeup'] += float(bool(scene.get('has_closeup', True))) * overlap
                bool_sums['has_high_motion'] += float(bool(scene.get('has_high_motion', False))) * overlap
                bool_sums['is_talking'] += float(bool(scene.get('is_talking', True))) * overlap

            if overlap_total > 0:
                windows.append({
                    'start_time': start,
                    'end_time': end,
                    'duration': end - start,
                    'face_count': sums['face_count'] / overlap_total,
                    'motion_score': sums['motion_score'] / overlap_total,
                    'visual_engagement': sums['visual_engagement'] / overlap_total,
                    'has_faces': (bool_sums['has_faces'] / overlap_total) >= 0.5,
                    'has_closeup': (bool_sums['has_closeup'] / overlap_total) >= 0.5,
                    'has_high_motion': (bool_sums['has_high_motion'] / overlap_total) >= 0.5,
                    'is_talking': (bool_sums['is_talking'] / overlap_total) >= 0.5,
                })
            start += step

        return windows
    
    def _analyze_scene_segment_fast(self, cap, start_time: float, end_time: float, fps: float, num_samples: int = 5) -> Dict:
        """
        Analyze a specific scene segment - FAST VERSION
        - Reduced frame samples
        - Downscaled images for face detection
        - Cached computations
        """
        # Sample frames from the scene
        sample_times = np.linspace(start_time, end_time, num_samples)
        
        face_detections = []
        motion_scores = []
        brightness_scores = []
        
        prev_frame = None
        
        # Downscale factor for face detection (faster but less accurate)
        downscale = 0.5  # Process at 50% resolution
        
        for sample_time in sample_times:
            # Seek to frame
            frame_number = int(sample_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Downscale for faster face detection
            small_gray = cv2.resize(gray, None, fx=downscale, fy=downscale)
            
            # Face detection on smaller image (faster)
            faces = self.face_cascade.detectMultiScale(
                small_gray, 
                scaleFactor=1.2,  # Less precise but faster
                minNeighbors=4,   # Slightly more lenient
                minSize=(int(20 * downscale), int(20 * downscale))
            )
            face_detections.append(len(faces))
            
            # Motion detection (if we have previous frame)
            if prev_frame is not None:
                # Use smaller region for motion calculation
                motion = cv2.absdiff(small_gray, prev_frame)
                motion_score = np.mean(motion)
                motion_scores.append(motion_score)
            
            # Brightness (from downscaled image is fine)
            brightness = np.mean(small_gray)
            brightness_scores.append(brightness)
            
            prev_frame = small_gray.copy()
        
        # Calculate averages with defaults
        avg_faces = float(np.mean(face_detections)) if face_detections else 0.5  # Assume face for monolog
        avg_motion = float(np.mean(motion_scores)) if motion_scores else 15.0
        avg_brightness = float(np.mean(brightness_scores)) if brightness_scores else 128.0
        
        # Determine if this is a close-up (more faces = likely close-up)
        has_closeup = avg_faces > 0.3  # More lenient for detection
        
        # High motion indicates active scene
        has_high_motion = avg_motion > 20
        
        return {
            'has_faces': avg_faces > 0,
            'face_count': avg_faces,
            'has_closeup': has_closeup,
            'motion_score': avg_motion,
            'has_high_motion': has_high_motion,
            'brightness': avg_brightness,
            'visual_engagement': self._calculate_visual_engagement(
                avg_faces, avg_motion, avg_brightness
            )
        }
    
    def _calculate_visual_engagement(self, faces: float, motion: float, brightness: float) -> float:
        """
        Calculate visual engagement score (0-1)
        Higher score = more engaging visuals
        Boosted baseline for monolog support
        """
        # Normalize values
        face_score = min(faces / 2.0, 1.0)  # 2+ faces = max score
        motion_score = min(motion / 50.0, 1.0)  # Motion > 50 = max score
        brightness_score = 1.0 - abs(brightness - 127) / 127  # Optimal brightness ~127
        
        # Weighted average with boosted baseline for monolog
        base_engagement = 0.3  # Minimum engagement score
        
        engagement = base_engagement + (
            face_score * 0.35 +      # Faces are most important
            motion_score * 0.2 +     # Motion adds interest
            brightness_score * 0.15  # Good lighting helps
        )
        
        return min(float(engagement), 1.0)
