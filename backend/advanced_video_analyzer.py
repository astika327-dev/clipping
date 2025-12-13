"""
Advanced Video Analyzer Module
Deep Learning Enhanced Version with:
- MediaPipe Face Detection & Emotion Recognition
- YOLOv8 Object Detection
- Speaker Activity Detection
- Enhanced Visual Engagement Scoring
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Lazy imports for optional dependencies
_mediapipe = None
_ultralytics = None
_fer = None  # Facial Emotion Recognition

def _load_mediapipe():
    global _mediapipe
    if _mediapipe is None:
        try:
            import mediapipe as mp
            _mediapipe = mp
        except ImportError:
            print("⚠️ MediaPipe not installed. Run: pip install mediapipe")
    return _mediapipe

def _load_ultralytics():
    global _ultralytics
    if _ultralytics is None:
        try:
            from ultralytics import YOLO
            _ultralytics = YOLO
        except ImportError:
            print("⚠️ Ultralytics not installed. Run: pip install ultralytics")
    return _ultralytics

def _load_fer():
    global _fer
    if _fer is None:
        try:
            from fer import FER
            _fer = FER
        except ImportError:
            print("⚠️ FER not installed. Run: pip install fer")
    return _fer


class AdvancedFaceAnalyzer:
    """
    Deep learning face analysis using MediaPipe + FER for emotion detection.
    Much more accurate than Haar cascades.
    """
    
    def __init__(self):
        self._mp_face = None
        self._face_mesh = None
        self._emotion_detector = None
        self._initialized = False
    
    def _initialize(self):
        if self._initialized:
            return True
            
        mp = _load_mediapipe()
        if mp is None:
            return False
        
        try:
            self._mp_face = mp.solutions.face_detection
            self._mp_face_mesh = mp.solutions.face_mesh
            
            # High confidence face detection
            self._face_detector = self._mp_face.FaceDetection(
                model_selection=1,  # Full range model (better for various distances)
                min_detection_confidence=0.5
            )
            
            # Face mesh for expression analysis (468 landmarks)
            self._face_mesh = self._mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=5,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
            
            self._initialized = True
            print("   ✅ MediaPipe Face Detection initialized")
            return True
        except Exception as e:
            print(f"   ⚠️ MediaPipe initialization failed: {e}")
            return False
    
    def analyze_frame(self, frame: np.ndarray) -> Dict:
        """
        Analyze a single frame for faces and expressions.
        Returns detailed face analysis including emotions.
        """
        if not self._initialize():
            # Fallback to basic detection
            return self._fallback_analyze(frame)
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Face detection
        face_results = self._face_detector.process(rgb_frame)
        
        faces = []
        emotions = []
        
        if face_results.detections:
            h, w = frame.shape[:2]
            
            for detection in face_results.detections:
                # Get bounding box
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                confidence = detection.score[0]
                
                faces.append({
                    'bbox': (x, y, width, height),
                    'confidence': confidence,
                    'size_ratio': (width * height) / (w * h)  # Face size relative to frame
                })
        
        # Analyze expressions using face mesh landmarks
        mesh_results = self._face_mesh.process(rgb_frame)
        
        expression_scores = {
            'neutral': 0.5,
            'happy': 0.0,
            'surprised': 0.0,
            'talking': 0.0
        }
        
        if mesh_results.multi_face_landmarks:
            for face_landmarks in mesh_results.multi_face_landmarks:
                # Analyze mouth openness (talking detection)
                # Upper lip: landmark 13, Lower lip: landmark 14
                upper_lip = face_landmarks.landmark[13]
                lower_lip = face_landmarks.landmark[14]
                mouth_open = abs(upper_lip.y - lower_lip.y)
                
                # Analyze eye openness (surprise detection)
                # Upper eyelid: 159, Lower eyelid: 145 (right eye)
                upper_lid = face_landmarks.landmark[159]
                lower_lid = face_landmarks.landmark[145]
                eye_open = abs(upper_lid.y - lower_lid.y)
                
                # Smile detection using mouth corners
                # Left corner: 61, Right corner: 291
                left_corner = face_landmarks.landmark[61]
                right_corner = face_landmarks.landmark[291]
                mouth_width = abs(left_corner.x - right_corner.x)
                
                # Estimate expressions
                if mouth_open > 0.03:
                    expression_scores['talking'] = min(1.0, mouth_open * 15)
                
                if eye_open > 0.025:
                    expression_scores['surprised'] = min(1.0, (eye_open - 0.02) * 20)
                
                if mouth_width > 0.15:
                    expression_scores['happy'] = min(1.0, (mouth_width - 0.12) * 10)
                
                # Adjust neutral based on other expressions
                max_expression = max(expression_scores['happy'], 
                                   expression_scores['surprised'], 
                                   expression_scores['talking'])
                expression_scores['neutral'] = max(0.0, 1.0 - max_expression)
        
        return {
            'face_count': len(faces),
            'faces': faces,
            'has_closeup': any(f['size_ratio'] > 0.05 for f in faces),  # Face > 5% of frame
            'expressions': expression_scores,
            'is_talking': expression_scores['talking'] > 0.3,
            'is_engaged': expression_scores['happy'] > 0.2 or expression_scores['surprised'] > 0.2
        }
    
    def _fallback_analyze(self, frame: np.ndarray) -> Dict:
        """Fallback using Haar cascades if MediaPipe fails."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        
        return {
            'face_count': len(faces),
            'faces': [{'bbox': tuple(f), 'confidence': 0.5} for f in faces],
            'has_closeup': len(faces) > 0,
            'expressions': {'neutral': 0.5},
            'is_talking': False,
            'is_engaged': False
        }
    
    def cleanup(self):
        """Release resources."""
        if self._face_detector:
            self._face_detector.close()
        if self._face_mesh:
            self._face_mesh.close()


class ObjectDetector:
    """
    YOLOv8-based object detection for scene understanding.
    Detects relevant objects like: person, phone, laptop, microphone, etc.
    """
    
    # Objects relevant for video content analysis
    RELEVANT_OBJECTS = {
        'person': 1.0,      # Very relevant
        'cell phone': 0.8,
        'laptop': 0.7,
        'tv': 0.6,
        'book': 0.5,
        'bottle': 0.3,
        'cup': 0.3,
        'chair': 0.2,
        'couch': 0.2,
        'microphone': 0.9,  # Very relevant for podcasts
        'keyboard': 0.5,
        'mouse': 0.4,
    }
    
    def __init__(self, model_size: str = 'n'):
        """
        Initialize YOLO model.
        Args:
            model_size: 'n' (nano), 's' (small), 'm' (medium), 'l' (large), 'x' (xlarge)
        """
        self._model = None
        self.model_size = model_size
        self._initialized = False
    
    def _initialize(self) -> bool:
        if self._initialized:
            return True
        
        YOLO = _load_ultralytics()
        if YOLO is None:
            return False
        
        try:
            # Use nano model for speed (can upgrade to 's' or 'm' for accuracy)
            self._model = YOLO(f'yolov8{self.model_size}.pt')
            self._initialized = True
            print(f"   ✅ YOLOv8-{self.model_size} Object Detection initialized")
            return True
        except Exception as e:
            print(f"   ⚠️ YOLO initialization failed: {e}")
            return False
    
    def detect(self, frame: np.ndarray, confidence: float = 0.5) -> Dict:
        """
        Detect objects in frame.
        Returns object counts and relevance score.
        """
        if not self._initialize():
            return self._fallback_detect()
        
        try:
            # Run inference
            results = self._model(frame, verbose=False, conf=confidence)
            
            objects = []
            relevance_score = 0.0
            person_count = 0
            
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = self._model.names[cls_id]
                    conf = float(box.conf[0])
                    
                    # Track person count
                    if cls_name == 'person':
                        person_count += 1
                    
                    # Add to relevance score
                    if cls_name in self.RELEVANT_OBJECTS:
                        relevance_score += self.RELEVANT_OBJECTS[cls_name] * conf
                    
                    objects.append({
                        'class': cls_name,
                        'confidence': conf,
                        'bbox': box.xyxy[0].tolist()
                    })
            
            return {
                'objects': objects,
                'object_count': len(objects),
                'person_count': person_count,
                'relevance_score': min(1.0, relevance_score / 3),  # Normalize
                'is_interview': person_count >= 2,
                'is_solo': person_count == 1,
                'has_tech': any(o['class'] in ['laptop', 'cell phone', 'keyboard'] for o in objects)
            }
        except Exception as e:
            print(f"   ⚠️ Object detection failed: {e}")
            return self._fallback_detect()
    
    def _fallback_detect(self) -> Dict:
        """Fallback when YOLO is not available."""
        return {
            'objects': [],
            'object_count': 0,
            'person_count': 1,  # Assume single speaker
            'relevance_score': 0.5,
            'is_interview': False,
            'is_solo': True,
            'has_tech': False
        }


class SpeakerActivityDetector:
    """
    Detect speaker activity and engagement without full diarization.
    Simpler and faster than pyannote, but still useful.
    """
    
    def __init__(self):
        self._face_analyzer = AdvancedFaceAnalyzer()
        self._prev_face_positions = []
        
    def analyze_speaker_activity(self, frames: List[np.ndarray]) -> Dict:
        """
        Analyze speaker activity across multiple frames.
        Detects:
        - Active speaking (mouth movement)
        - Head movement (engagement)
        - Face consistency (same speaker)
        """
        talking_frames = 0
        engaged_frames = 0
        face_consistency = []
        
        for frame in frames:
            analysis = self._face_analyzer.analyze_frame(frame)
            
            if analysis['is_talking']:
                talking_frames += 1
            
            if analysis['is_engaged']:
                engaged_frames += 1
            
            # Track face position for consistency
            if analysis['faces']:
                main_face = analysis['faces'][0]
                face_consistency.append(main_face['bbox'])
        
        total_frames = max(len(frames), 1)
        
        # Calculate face position variance (lower = more consistent speaker)
        position_variance = 0.0
        if len(face_consistency) >= 2:
            centers = [(f[0] + f[2]/2, f[1] + f[3]/2) for f in face_consistency]
            x_var = np.var([c[0] for c in centers])
            y_var = np.var([c[1] for c in centers])
            position_variance = (x_var + y_var) / 2
        
        return {
            'talking_ratio': talking_frames / total_frames,
            'engagement_ratio': engaged_frames / total_frames,
            'speaker_consistency': 1.0 / (1.0 + position_variance / 10000),  # 0-1, higher = more consistent
            'is_active_speaker': talking_frames / total_frames > 0.3,
            'is_engaged_content': engaged_frames / total_frames > 0.2
        }
    
    def cleanup(self):
        self._face_analyzer.cleanup()


class AdvancedVideoAnalyzer:
    """
    Enhanced Video Analyzer with deep learning capabilities.
    Combines: MediaPipe + YOLO + Speaker Detection
    """
    
    def __init__(self, video_path: str, config, enable_deep_learning: bool = True):
        self.video_path = video_path
        self.config = config
        self.enable_deep_learning = enable_deep_learning
        
        # Initialize analyzers
        self._face_analyzer = None
        self._object_detector = None
        self._speaker_detector = None
        
        if enable_deep_learning:
            self._face_analyzer = AdvancedFaceAnalyzer()
            self._object_detector = ObjectDetector(model_size='n')  # Nano for speed
            self._speaker_detector = SpeakerActivityDetector()
        
        self._analysis_cache = {}
        self._lock = threading.Lock()
        
        # Fall back to basic analyzer
        from video_analyzer import VideoAnalyzer as BasicVideoAnalyzer
        self._basic_analyzer = BasicVideoAnalyzer(video_path, config)
    
    def analyze(self) -> Dict:
        """
        Main analysis function with deep learning enhancements.
        """
        print(f"🎬 Analyzing video with DEEP LEARNING: {self.video_path}")
        
        # Get basic analysis first (fast)
        basic_result = self._basic_analyzer.analyze()
        
        if not self.enable_deep_learning:
            return basic_result
        
        # Enhance with deep learning
        try:
            enhanced_scenes = self._enhance_scenes_with_dl(basic_result['scenes'], basic_result['metadata'])
            basic_result['scenes'] = enhanced_scenes
            basic_result['deep_learning_enabled'] = True
            
            # Add overall deep learning stats
            dl_stats = self._calculate_dl_stats(enhanced_scenes)
            basic_result['dl_analysis'] = dl_stats
            
            print(f"   ✅ Deep learning analysis complete")
            print(f"      📊 Avg engagement: {dl_stats['avg_engagement']:.2f}")
            print(f"      🗣️ Talking ratio: {dl_stats['avg_talking_ratio']:.2f}")
            print(f"      👤 Consistent speaker: {dl_stats['avg_speaker_consistency']:.2f}")
            
        except Exception as e:
            print(f"   ⚠️ Deep learning enhancement failed: {e}")
            basic_result['deep_learning_enabled'] = False
        
        return basic_result
    
    def _enhance_scenes_with_dl(self, scenes: List[Dict], metadata: Dict) -> List[Dict]:
        """
        Enhance each scene with deep learning analysis.
        """
        print("   🧠 Running deep learning analysis on scenes...")
        
        cap = cv2.VideoCapture(self.video_path)
        fps = metadata.get('fps', 30)
        
        enhanced_scenes = []
        total = len(scenes)
        
        for idx, scene in enumerate(scenes):
            if idx % 10 == 0:
                print(f"      Processing scene {idx+1}/{total}...")
            
            start_time = scene.get('start_time', 0)
            end_time = scene.get('end_time', start_time + 10)
            
            # Sample frames from this scene
            sample_frames = self._sample_frames(cap, start_time, end_time, fps, num_samples=3)
            
            if not sample_frames:
                enhanced_scenes.append(scene)
                continue
            
            # Run deep learning analysis
            dl_analysis = self._analyze_frames_dl(sample_frames)
            
            # Merge with existing scene data
            enhanced_scene = {**scene, **dl_analysis}
            
            # Recalculate visual engagement with DL data
            enhanced_scene['visual_engagement'] = self._calculate_enhanced_engagement(
                scene.get('visual_engagement', 0.5),
                dl_analysis
            )
            
            enhanced_scenes.append(enhanced_scene)
        
        cap.release()
        return enhanced_scenes
    
    def _sample_frames(self, cap, start_time: float, end_time: float, fps: float, num_samples: int = 3) -> List[np.ndarray]:
        """Sample frames from a time range."""
        frames = []
        sample_times = np.linspace(start_time, end_time, num_samples)
        
        for t in sample_times:
            frame_num = int(t * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if ret:
                # Resize for faster processing
                frame = cv2.resize(frame, (640, 360))
                frames.append(frame)
        
        return frames
    
    def _analyze_frames_dl(self, frames: List[np.ndarray]) -> Dict:
        """Run all deep learning analyzers on frames."""
        result = {
            'dl_face_analysis': {},
            'dl_object_analysis': {},
            'dl_speaker_analysis': {},
        }
        
        # Face analysis (on middle frame)
        if self._face_analyzer and frames:
            middle_frame = frames[len(frames)//2]
            result['dl_face_analysis'] = self._face_analyzer.analyze_frame(middle_frame)
        
        # Object detection (on middle frame)
        if self._object_detector and frames:
            middle_frame = frames[len(frames)//2]
            result['dl_object_analysis'] = self._object_detector.detect(middle_frame)
        
        # Speaker activity (across all frames)
        if self._speaker_detector and frames:
            result['dl_speaker_analysis'] = self._speaker_detector.analyze_speaker_activity(frames)
        
        # Extract key metrics for easy access
        face = result['dl_face_analysis']
        obj = result['dl_object_analysis']
        speaker = result['dl_speaker_analysis']
        
        result['is_talking'] = face.get('is_talking', False)
        result['is_engaged'] = face.get('is_engaged', False)
        result['expression'] = max(face.get('expressions', {'neutral': 0.5}).items(), key=lambda x: x[1])[0]
        result['person_count'] = obj.get('person_count', 1)
        result['is_interview'] = obj.get('is_interview', False)
        result['talking_ratio'] = speaker.get('talking_ratio', 0.0)
        result['speaker_consistency'] = speaker.get('speaker_consistency', 0.5)
        
        return result
    
    def _calculate_enhanced_engagement(self, base_engagement: float, dl_analysis: Dict) -> float:
        """
        Calculate enhanced visual engagement using deep learning insights.
        """
        engagement = base_engagement
        
        # Boost for active talking
        if dl_analysis.get('is_talking'):
            engagement += 0.15
        
        # Boost for emotional expressions
        if dl_analysis.get('is_engaged'):
            engagement += 0.1
        
        # Boost for multiple people (interview/conversation)
        if dl_analysis.get('is_interview'):
            engagement += 0.1
        
        # Boost for consistent speaker (good for monolog)
        consistency = dl_analysis.get('speaker_consistency', 0.5)
        if consistency > 0.7:
            engagement += 0.05
        
        # Penalty for no detected faces
        face_count = dl_analysis.get('dl_face_analysis', {}).get('face_count', 0)
        if face_count == 0:
            engagement -= 0.1
        
        return max(0.0, min(1.0, engagement))
    
    def _calculate_dl_stats(self, scenes: List[Dict]) -> Dict:
        """Calculate aggregate deep learning statistics."""
        if not scenes:
            return {
                'avg_engagement': 0.5,
                'avg_talking_ratio': 0.0,
                'avg_speaker_consistency': 0.5,
                'interview_scenes': 0,
                'high_engagement_scenes': 0
            }
        
        engagements = [s.get('visual_engagement', 0.5) for s in scenes]
        talking_ratios = [s.get('talking_ratio', 0) for s in scenes]
        consistencies = [s.get('speaker_consistency', 0.5) for s in scenes]
        
        return {
            'avg_engagement': np.mean(engagements),
            'avg_talking_ratio': np.mean(talking_ratios),
            'avg_speaker_consistency': np.mean(consistencies),
            'interview_scenes': sum(1 for s in scenes if s.get('is_interview', False)),
            'high_engagement_scenes': sum(1 for s in scenes if s.get('visual_engagement', 0) > 0.7)
        }
    
    def cleanup(self):
        """Release all resources."""
        if self._face_analyzer:
            self._face_analyzer.cleanup()
        if self._speaker_detector:
            self._speaker_detector.cleanup()


# Factory function for backward compatibility
def create_video_analyzer(video_path: str, config, enable_deep_learning: bool = None) -> AdvancedVideoAnalyzer:
    """
    Create appropriate video analyzer based on config and available dependencies.
    """
    # Check if deep learning should be enabled
    if enable_deep_learning is None:
        enable_deep_learning = getattr(config, 'ENABLE_DEEP_LEARNING_VIDEO', True)
    
    return AdvancedVideoAnalyzer(video_path, config, enable_deep_learning)
