"""
Video Analyzer Module
Handles video analysis including scene detection, face detection, and visual analysis
"""
import cv2
import numpy as np
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
import os
from typing import List, Dict, Tuple

class VideoAnalyzer:
    def __init__(self, video_path: str, config):
        self.video_path = video_path
        self.config = config
        self.scenes = []
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
    def analyze(self) -> Dict:
        """
        Main analysis function
        Returns comprehensive video analysis
        """
        print(f"🎬 Analyzing video: {self.video_path}")
        
        # Get video metadata
        metadata = self._get_video_metadata()
        
        # Detect scenes
        scenes = self._detect_scenes()
        
        # Analyze each scene
        scene_analysis = self._analyze_scenes(scenes)
        
        return {
            'metadata': metadata,
            'scenes': scene_analysis,
            'total_scenes': len(scene_analysis)
        }
    
    def _get_video_metadata(self) -> Dict:
        """Get basic video information"""
        cap = cv2.VideoCapture(self.video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': duration,
            'aspect_ratio': f"{width}:{height}"
        }
    
    def _detect_scenes(self) -> List[Tuple[float, float]]:
        """
        Detect scene changes in video
        Returns list of (start_time, end_time) tuples
        """
        print("🔍 Detecting scenes...")
        
        video_manager = VideoManager([self.video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(
            ContentDetector(threshold=self.config.SCENE_THRESHOLD)
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
    
    def _analyze_scenes(self, scenes: List[Tuple[float, float]]) -> List[Dict]:
        """
        Analyze each scene for visual features
        """
        print("🎭 Analyzing scene content...")
        
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        scene_analysis = []
        
        for idx, (start_time, end_time) in enumerate(scenes):
            print(f"  Scene {idx + 1}/{len(scenes)}: {start_time:.2f}s - {end_time:.2f}s")
            
            # Sample frames from this scene
            analysis = self._analyze_scene_segment(cap, start_time, end_time, fps)
            
            scene_analysis.append({
                'scene_id': idx,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                **analysis
            })
        
        cap.release()
        
        return scene_analysis
    
    def _analyze_scene_segment(self, cap, start_time: float, end_time: float, fps: float) -> Dict:
        """
        Analyze a specific scene segment
        """
        # Sample 5 frames from the scene
        sample_times = np.linspace(start_time, end_time, 5)
        
        face_detections = []
        motion_scores = []
        brightness_scores = []
        
        prev_frame = None
        
        for sample_time in sample_times:
            # Seek to frame
            frame_number = int(sample_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Face detection
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            face_detections.append(len(faces))
            
            # Motion detection (if we have previous frame)
            if prev_frame is not None:
                motion = cv2.absdiff(gray, prev_frame)
                motion_score = np.mean(motion)
                motion_scores.append(motion_score)
            
            # Brightness
            brightness = np.mean(gray)
            brightness_scores.append(brightness)
            
            prev_frame = gray.copy()
        
        # Calculate averages
        avg_faces = np.mean(face_detections) if face_detections else 0
        avg_motion = np.mean(motion_scores) if motion_scores else 0
        avg_brightness = np.mean(brightness_scores) if brightness_scores else 0
        
        # Determine if this is a close-up (more faces = likely close-up)
        has_closeup = avg_faces > 0.5
        
        # High motion indicates active scene
        has_high_motion = avg_motion > 20
        
        return {
            'has_faces': avg_faces > 0,
            'face_count': avg_faces,
            'has_closeup': has_closeup,
            'motion_score': float(avg_motion),
            'has_high_motion': has_high_motion,
            'brightness': float(avg_brightness),
            'visual_engagement': self._calculate_visual_engagement(
                avg_faces, avg_motion, avg_brightness
            )
        }
    
    def _calculate_visual_engagement(self, faces: float, motion: float, brightness: float) -> float:
        """
        Calculate visual engagement score (0-1)
        Higher score = more engaging visuals
        """
        # Normalize values
        face_score = min(faces / 2.0, 1.0)  # 2+ faces = max score
        motion_score = min(motion / 50.0, 1.0)  # Motion > 50 = max score
        brightness_score = 1.0 - abs(brightness - 127) / 127  # Optimal brightness ~127
        
        # Weighted average
        engagement = (
            face_score * 0.5 +      # Faces are most important
            motion_score * 0.3 +    # Motion adds interest
            brightness_score * 0.2  # Good lighting helps
        )
        
        return float(engagement)
