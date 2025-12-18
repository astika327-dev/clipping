"""
Enterprise Features Module
Top-Tier AI Video Clipping Features inspired by Opus Clip, Vizard, and Munch

Features:
1. Enhanced Virality Score Algorithm
2. Smart Auto-Reframe (Speaker Focus)
3. Animated Captions System
4. AI-Powered Hook Generator
5. Filler Word Removal
6. Engagement Prediction Model
7. Trend Alignment Score
"""

import re
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CaptionStyle(Enum):
    """Caption animation styles inspired by top creators"""
    HORMOZI = "hormozi"      # Bold, word-by-word highlight
    MRBEAST = "mrbeast"      # Colorful, emoji-rich
    MINIMAL = "minimal"      # Clean, simple
    PODCAST = "podcast"      # Two-speaker optimized
    VIRAL = "viral"          # Maximum engagement


@dataclass
class ViralityMetrics:
    """Comprehensive virality scoring metrics"""
    hook_strength: float = 0.0        # 0-1: How strong is the opening
    emotional_arc: float = 0.0        # 0-1: Emotional journey score
    speech_pacing: float = 0.0        # 0-1: Optimal WPM score
    retention_prediction: float = 0.0  # 0-1: Predicted watch-through rate
    trend_alignment: float = 0.0       # 0-1: Match with current trends
    engagement_velocity: float = 0.0   # 0-1: Predicted engagement speed
    shareability: float = 0.0          # 0-1: Likelihood of shares
    overall_score: float = 0.0         # 0-1: Combined weighted score


class EnhancedViralityScorer:
    """
    Advanced Virality Score Algorithm
    Based on analysis of Opus Clip's methodology and viral video patterns
    """
    
    # Trending topics and keywords (updated regularly in production)
    TRENDING_TOPICS_2024 = {
        'id': [
            'mindset', 'cuan', 'passive income', 'investasi', 'crypto',
            'AI', 'chatgpt', 'side hustle', 'financial freedom', 'scaling',
            'mental health', 'produktivitas', 'hustle culture', 'burnout',
            'relationship', 'toxic', 'red flag', 'green flag', 'healing'
        ],
        'en': [
            'mindset', 'money', 'passive income', 'investment', 'crypto',
            'AI', 'chatgpt', 'side hustle', 'financial freedom', 'scaling',
            'mental health', 'productivity', 'hustle culture', 'burnout',
            'relationship', 'toxic', 'red flag', 'green flag', 'healing'
        ]
    }
    
    # Hook patterns that perform well
    STRONG_HOOK_PATTERNS = [
        # Curiosity gap
        r'(?:rahasia|secret|truth|fakta|shocking)',
        r'(?:gak|tidak|never|jangan)\s+(?:ada|pernah|akan)',
        r'(?:ini|this)\s+(?:yang|is|akan)',
        # Direct address
        r'^(?:kamu|you|lu|lo|anda)\s+',
        r'^(?:dengerin|listen|perhatikan|watch)',
        # Numbers and lists
        r'^\d+\s+(?:cara|tips|alasan|reasons|ways)',
        r'(?:nomor|number)\s+\d+',
        # Controversy/challenge
        r'(?:salah|wrong|mistake|error)',
        r'(?:stop|berhenti|quit)\s+(?:doing|melakukan)',
        # Story hooks
        r'^(?:waktu|when|saat)\s+(?:itu|that|gue|i)',
        r'^(?:jadi|so)\s+(?:ceritanya|basically)',
    ]
    
    # Emotional arc indicators
    EMOTIONAL_MARKERS = {
        'tension_build': ['tapi', 'but', 'namun', 'however', 'sayangnya', 'unfortunately'],
        'climax': ['ternyata', 'turns out', 'akhirnya', 'finally', 'boom', 'dan', 'then'],
        'resolution': ['jadi', 'so', 'intinya', 'kesimpulannya', 'the point is', 'moral']
    }
    
    def __init__(self, language: str = 'id'):
        self.language = language
        self.trending_topics = self.TRENDING_TOPICS_2024.get(language, self.TRENDING_TOPICS_2024['id'])
    
    def calculate_comprehensive_score(self, segment: Dict) -> ViralityMetrics:
        """Calculate all virality metrics for a segment"""
        text = (segment.get('text') or '').lower().strip()
        duration = segment.get('duration', 0)
        
        metrics = ViralityMetrics()
        
        # 1. Hook Strength (first 5 seconds / ~15 words)
        metrics.hook_strength = self._calculate_hook_strength(text)
        
        # 2. Emotional Arc
        metrics.emotional_arc = self._calculate_emotional_arc(text)
        
        # 3. Speech Pacing (WPM)
        metrics.speech_pacing = self._calculate_pacing_score(text, duration)
        
        # 4. Retention Prediction
        metrics.retention_prediction = self._predict_retention(text, duration)
        
        # 5. Trend Alignment
        metrics.trend_alignment = self._calculate_trend_alignment(text)
        
        # 6. Engagement Velocity Prediction
        metrics.engagement_velocity = self._predict_engagement_velocity(text, segment)
        
        # 7. Shareability
        metrics.shareability = self._calculate_shareability(text)
        
        # Calculate overall score with weights
        metrics.overall_score = self._calculate_weighted_score(metrics)
        
        return metrics
    
    def _calculate_hook_strength(self, text: str) -> float:
        """Analyze the first portion of text for hook quality"""
        if not text:
            return 0.0
        
        # Get first ~50 characters or first sentence
        first_part = text[:100].split('.')[0] if '.' in text[:100] else text[:100]
        
        score = 0.3  # Base score
        
        # Check against strong hook patterns
        for pattern in self.STRONG_HOOK_PATTERNS:
            if re.search(pattern, first_part, re.IGNORECASE):
                score += 0.15
        
        # Bonus for questions (engagement driver)
        if '?' in first_part:
            score += 0.1
        
        # Bonus for direct address
        if any(word in first_part for word in ['kamu', 'you', 'lu', 'lo', 'anda']):
            score += 0.1
        
        # Bonus for numbers (specificity)
        if re.search(r'\d+', first_part):
            score += 0.08
        
        # Penalty for weak starts
        weak_starts = ['jadi', 'so', 'um', 'eh', 'oke', 'okay', 'nah']
        if any(first_part.startswith(w) for w in weak_starts):
            score -= 0.15
        
        return min(1.0, max(0.0, score))
    
    def _calculate_emotional_arc(self, text: str) -> float:
        """Detect emotional journey in content"""
        if not text:
            return 0.0
        
        score = 0.2  # Base
        
        has_tension = any(m in text for m in self.EMOTIONAL_MARKERS['tension_build'])
        has_climax = any(m in text for m in self.EMOTIONAL_MARKERS['climax'])
        has_resolution = any(m in text for m in self.EMOTIONAL_MARKERS['resolution'])
        
        # Complete arc gets highest score
        if has_tension and has_climax and has_resolution:
            score = 0.95
        elif has_tension and has_climax:
            score = 0.75
        elif has_climax and has_resolution:
            score = 0.65
        elif has_climax:
            score = 0.5
        elif has_tension or has_resolution:
            score = 0.35
        
        return score
    
    def _calculate_pacing_score(self, text: str, duration: float) -> float:
        """Calculate optimal speech pacing score"""
        if not text or duration <= 0:
            return 0.5
        
        words = len(text.split())
        wpm = (words / duration) * 60
        
        # Optimal WPM range for viral content: 140-180
        if 140 <= wpm <= 180:
            return 1.0
        elif 120 <= wpm < 140 or 180 < wpm <= 200:
            return 0.8
        elif 100 <= wpm < 120 or 200 < wpm <= 220:
            return 0.6
        elif wpm < 100:
            return 0.3  # Too slow
        else:
            return 0.4  # Too fast
    
    def _predict_retention(self, text: str, duration: float) -> float:
        """Predict audience retention rate"""
        if not text:
            return 0.3
        
        score = 0.5  # Base
        
        # Shorter clips have higher retention
        if duration <= 15:
            score += 0.2
        elif duration <= 30:
            score += 0.1
        elif duration > 45:
            score -= 0.1
        
        # Content completeness
        if text.rstrip().endswith(('.', '!', '?')):
            score += 0.1  # Complete thought
        
        # Avoid abrupt endings
        incomplete_endings = ['dan', 'tapi', 'karena', 'jadi', 'and', 'but', 'because', 'so']
        if any(text.rstrip().endswith(w) for w in incomplete_endings):
            score -= 0.15
        
        # CTA presence boosts retention
        cta_words = ['share', 'like', 'comment', 'follow', 'subscribe', 'bagikan', 'komen']
        if any(w in text for w in cta_words):
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_trend_alignment(self, text: str) -> float:
        """Score how well content aligns with current trends"""
        if not text:
            return 0.0
        
        matches = sum(1 for topic in self.trending_topics if topic in text)
        
        if matches >= 3:
            return 0.95
        elif matches >= 2:
            return 0.75
        elif matches >= 1:
            return 0.5
        return 0.2
    
    def _predict_engagement_velocity(self, text: str, segment: Dict) -> float:
        """Predict how fast the content will get engagement"""
        score = 0.4  # Base
        
        # Controversial/polarizing content spreads faster
        controversy_words = ['salah', 'wrong', 'toxic', 'bohong', 'lie', 'scam']
        if any(w in text for w in controversy_words):
            score += 0.2
        
        # Relatable content
        relatable_words = ['kita semua', 'we all', 'pernah', 'ever', 'relate', 'sama']
        if any(w in text for w in relatable_words):
            score += 0.15
        
        # Visual engagement (from segment metadata)
        if segment.get('visual', {}).get('has_faces'):
            score += 0.1
        if segment.get('is_conversation'):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_shareability(self, text: str) -> float:
        """Predict likelihood of shares"""
        if not text:
            return 0.2
        
        score = 0.3  # Base
        
        # Quotable content
        if len(text.split()) <= 30:  # Short and punchy
            score += 0.15
        
        # Contains memorable phrase patterns
        memorable_patterns = [
            r'(?:remember|ingat)\s+(?:this|ini)',
            r'(?:the|yang)\s+(?:key|kunci|secret|rahasia)',
            r'(?:rule|aturan)\s+(?:number|nomor)?\s*\d',
            r'(?:never|jangan\s+pernah)',
            r'(?:always|selalu)',
        ]
        for pattern in memorable_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.12
        
        # Has call to action
        if any(w in text for w in ['share', 'tag', 'bagikan', 'tandai']):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_weighted_score(self, metrics: ViralityMetrics) -> float:
        """Calculate final weighted score"""
        weights = {
            'hook_strength': 0.25,       # Most important
            'emotional_arc': 0.15,
            'speech_pacing': 0.10,
            'retention_prediction': 0.15,
            'trend_alignment': 0.10,
            'engagement_velocity': 0.15,
            'shareability': 0.10
        }
        
        weighted_sum = (
            metrics.hook_strength * weights['hook_strength'] +
            metrics.emotional_arc * weights['emotional_arc'] +
            metrics.speech_pacing * weights['speech_pacing'] +
            metrics.retention_prediction * weights['retention_prediction'] +
            metrics.trend_alignment * weights['trend_alignment'] +
            metrics.engagement_velocity * weights['engagement_velocity'] +
            metrics.shareability * weights['shareability']
        )
        
        return round(weighted_sum, 3)


class SmartAutoReframe:
    """
    Smart Auto-Reframe System
    Automatically centers on active speaker for optimal framing
    """
    
    ASPECT_RATIOS = {
        'tiktok': (9, 16),    # 9:16 vertical
        'reels': (9, 16),     # 9:16 vertical
        'shorts': (9, 16),    # 9:16 vertical
        'square': (1, 1),     # 1:1 square
        'youtube': (16, 9),   # 16:9 horizontal
    }
    
    def __init__(self):
        self.current_speaker = None
        self.speaker_positions = {}
    
    def calculate_crop_region(
        self,
        frame_width: int,
        frame_height: int,
        faces: List[Dict],
        target_ratio: str = 'tiktok',
        smooth_transition: bool = True
    ) -> Dict:
        """
        Calculate optimal crop region based on speaker positions
        
        Returns:
            Dict with x, y, width, height for crop region
        """
        ratio = self.ASPECT_RATIOS.get(target_ratio, (9, 16))
        target_w_ratio, target_h_ratio = ratio
        
        # Calculate target dimensions maintaining aspect ratio
        if frame_width / frame_height > target_w_ratio / target_h_ratio:
            # Video is wider than target - crop width
            crop_height = frame_height
            crop_width = int(frame_height * target_w_ratio / target_h_ratio)
        else:
            # Video is taller than target - crop height
            crop_width = frame_width
            crop_height = int(frame_width * target_h_ratio / target_w_ratio)
        
        # Find active speaker (the one who's talking)
        active_speaker = None
        for face in faces:
            if face.get('expressions', {}).get('talking', 0) > 0.3:
                active_speaker = face
                break
        
        # If no active speaker, center on largest face
        if not active_speaker and faces:
            active_speaker = max(faces, key=lambda f: f.get('size_ratio', 0))
        
        # Calculate center point
        if active_speaker:
            bbox = active_speaker.get('bbox', [0.5, 0.5, 0.2, 0.2])
            center_x = int((bbox[0] + bbox[2] / 2) * frame_width)
            center_y = int((bbox[1] + bbox[3] / 2) * frame_height)
        else:
            # Default to center of frame
            center_x = frame_width // 2
            center_y = frame_height // 2
        
        # Calculate crop region centered on speaker
        x = max(0, min(center_x - crop_width // 2, frame_width - crop_width))
        y = max(0, min(center_y - crop_height // 2, frame_height - crop_height))
        
        return {
            'x': x,
            'y': y,
            'width': crop_width,
            'height': crop_height,
            'center_x': center_x,
            'center_y': center_y,
            'target_ratio': target_ratio,
            'active_speaker': active_speaker is not None
        }
    
    def generate_reframe_keyframes(
        self,
        timeline: List[Dict],
        frame_width: int,
        frame_height: int,
        target_ratio: str = 'tiktok'
    ) -> List[Dict]:
        """
        Generate keyframes for smooth reframing throughout the clip
        """
        keyframes = []
        prev_region = None
        
        for point in timeline:
            timestamp = point.get('timestamp', 0)
            faces = point.get('faces', [])
            
            region = self.calculate_crop_region(
                frame_width, frame_height, faces, target_ratio
            )
            region['timestamp'] = timestamp
            
            # Add smooth transition logic
            if prev_region:
                # Calculate distance moved
                dist = abs(region['center_x'] - prev_region['center_x'])
                
                # Only add keyframe if significant movement
                if dist > frame_width * 0.1:  # 10% of frame width
                    keyframes.append(region)
            else:
                keyframes.append(region)
            
            prev_region = region
        
        return keyframes


class AnimatedCaptionGenerator:
    """
    Animated Caption System
    Generate word-by-word animated captions like Hormozi/MrBeast style
    """
    
    STYLE_CONFIGS = {
        CaptionStyle.HORMOZI: {
            'font': 'Impact',
            'size': 72,
            'color': '#FFFFFF',
            'highlight_color': '#FFD700',
            'bg_color': 'black@0.7',
            'animation': 'pop',
            'word_duration': 0.3,
            'position': 'center'
        },
        CaptionStyle.MRBEAST: {
            'font': 'Montserrat-Bold',
            'size': 64,
            'color': '#FFFFFF',
            'highlight_color': '#FF0000',
            'bg_color': 'none',
            'animation': 'bounce',
            'word_duration': 0.25,
            'position': 'bottom',
            'use_emoji': True
        },
        CaptionStyle.MINIMAL: {
            'font': 'Inter',
            'size': 48,
            'color': '#FFFFFF',
            'highlight_color': '#4A90D9',
            'bg_color': 'black@0.5',
            'animation': 'fade',
            'word_duration': 0.4,
            'position': 'bottom'
        },
        CaptionStyle.PODCAST: {
            'font': 'Roboto',
            'size': 56,
            'color': '#FFFFFF',
            'highlight_color': '#00FF00',
            'bg_color': 'black@0.6',
            'animation': 'typewriter',
            'word_duration': 0.35,
            'position': 'bottom'
        },
        CaptionStyle.VIRAL: {
            'font': 'Poppins-Bold',
            'size': 68,
            'color': '#FFFFFF',
            'highlight_color': '#FF4500',
            'bg_color': 'black@0.8',
            'animation': 'shake',
            'word_duration': 0.2,
            'position': 'center',
            'use_emoji': True
        }
    }
    
    # Keywords to highlight
    HIGHLIGHT_KEYWORDS = [
        # Power words
        'uang', 'money', 'cuan', 'profit', 'income',
        'rahasia', 'secret', 'truth', 'fakta',
        'sukses', 'success', 'winning', 'menang',
        'gagal', 'fail', 'failure', 'kalah',
        # Numbers
        r'\d+%', r'\$\d+', r'Rp\s*[\d,.]+',
        # Emphasis  
        'penting', 'important', 'crucial', 'key',
        'never', 'always', 'jangan', 'harus',
        # Emotional
        'love', 'hate', 'cinta', 'benci',
        'amazing', 'terrible', 'luar biasa', 'parah'
    ]
    
    # Emoji mappings
    EMOJI_KEYWORDS = {
        'money': '💰', 'uang': '💰', 'cuan': '💸',
        'fire': '🔥', 'hot': '🔥', 'viral': '🔥',
        'love': '❤️', 'cinta': '❤️',
        'idea': '💡', 'tips': '💡',
        'warning': '⚠️', 'hati-hati': '⚠️',
        'success': '🏆', 'sukses': '🏆',
        'fail': '❌', 'gagal': '❌',
        'time': '⏰', 'waktu': '⏰',
        'grow': '📈', 'naik': '📈',
        'down': '📉', 'turun': '📉',
        'think': '🧠', 'pikir': '🧠',
        'speak': '🗣️', 'bicara': '🗣️'
    }
    
    def __init__(self, style: CaptionStyle = CaptionStyle.HORMOZI):
        self.style = style
        self.config = self.STYLE_CONFIGS[style]
    
    def generate_caption_data(
        self,
        transcript_segments: List[Dict],
        clip_start: float,
        clip_end: float
    ) -> List[Dict]:
        """
        Generate word-by-word caption data with timing and styling
        """
        captions = []
        
        for segment in transcript_segments:
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', 0)
            
            # Skip if segment is outside clip range
            if seg_end < clip_start or seg_start > clip_end:
                continue
            
            # Get words with timing if available
            words = segment.get('words', [])
            if not words:
                # Fallback: split text and estimate timing
                text = segment.get('text', '')
                words = self._estimate_word_timing(text, seg_start, seg_end)
            
            for word_data in words:
                word = word_data.get('word', word_data.get('text', ''))
                word_start = word_data.get('start', seg_start)
                word_end = word_data.get('end', word_start + 0.3)
                
                # Adjust timing relative to clip
                relative_start = word_start - clip_start
                relative_end = word_end - clip_start
                
                if relative_start < 0:
                    continue
                if relative_start > (clip_end - clip_start):
                    break
                
                caption_entry = {
                    'word': word,
                    'start': relative_start,
                    'end': relative_end,
                    'style': self._get_word_style(word)
                }
                
                captions.append(caption_entry)
        
        return captions
    
    def _estimate_word_timing(self, text: str, start: float, end: float) -> List[Dict]:
        """Estimate word timing when not available"""
        words = text.split()
        if not words:
            return []
        
        duration = end - start
        word_duration = duration / len(words)
        
        result = []
        current_time = start
        
        for word in words:
            result.append({
                'word': word,
                'start': current_time,
                'end': current_time + word_duration
            })
            current_time += word_duration
        
        return result
    
    def _get_word_style(self, word: str) -> Dict:
        """Determine special styling for a word"""
        word_lower = word.lower().strip('.,!?')
        
        style = {
            'highlight': False,
            'emoji': None,
            'animation': self.config['animation']
        }
        
        # Check if word should be highlighted
        for keyword in self.HIGHLIGHT_KEYWORDS:
            if isinstance(keyword, str):
                if keyword in word_lower:
                    style['highlight'] = True
                    break
            else:
                # Regex pattern
                if re.search(keyword, word):
                    style['highlight'] = True
                    break
        
        # Add emoji if enabled
        if self.config.get('use_emoji'):
            for key, emoji in self.EMOJI_KEYWORDS.items():
                if key in word_lower:
                    style['emoji'] = emoji
                    break
        
        return style
    
    def generate_ffmpeg_filter(self, captions: List[Dict], video_width: int, video_height: int) -> str:
        """
        Generate FFmpeg filter complex for animated captions
        """
        filters = []
        
        font_size = self.config['size']
        font_color = self.config['color']
        highlight_color = self.config['highlight_color']
        
        # Position calculation
        if self.config['position'] == 'center':
            y_pos = f"(h-text_h)/2"
        elif self.config['position'] == 'top':
            y_pos = "h*0.15"
        else:  # bottom
            y_pos = "h*0.80"
        
        for caption in captions:
            word = caption['word'].replace("'", "\\'").replace(":", "\\:")
            start = caption['start']
            end = caption['end']
            style = caption['style']
            
            color = highlight_color if style['highlight'] else font_color
            
            # Add emoji if present
            display_text = f"{style['emoji']} {word}" if style.get('emoji') else word
            
            filter_str = (
                f"drawtext=text='{display_text}':"
                f"fontsize={font_size}:"
                f"fontcolor={color}:"
                f"x=(w-text_w)/2:y={y_pos}:"
                f"enable='between(t,{start:.2f},{end:.2f})'"
            )
            
            filters.append(filter_str)
        
        return ','.join(filters)


class FillerWordRemover:
    """
    Filler Word Detection and Removal System
    Identifies and marks filler words for audio editing
    """
    
    FILLER_PATTERNS = {
        'id': [
            'ehm', 'emm', 'umm', 'uh', 'um', 'eh', 'ah',
            'anu', 'eee', 'mmm', 'hmm',
            'gitu', 'gitu loh', 'gitu ya', 'gitu kan',
            'kayak', 'kayaknya', 'kayak gitu',
            'ya kan', 'kan ya', 'kan',
            'apa ya', 'apa namanya', 'apa sih',
            'pokoknya', 'intinya', 'basically',
            'sebenernya', 'sebenarnya'
        ],
        'en': [
            'um', 'uh', 'uhm', 'ah', 'eh', 'hmm', 'mm',
            'like', 'you know', 'i mean', 'basically',
            'actually', 'literally', 'kind of', 'sort of',
            'right', 'okay so', 'so yeah', 'yeah so',
            'anyway', 'anyways'
        ]
    }
    
    def __init__(self, language: str = 'id'):
        self.language = language
        self.fillers = self.FILLER_PATTERNS.get(language, self.FILLER_PATTERNS['id'])
    
    def detect_fillers(self, transcript_segments: List[Dict]) -> List[Dict]:
        """
        Detect filler words and return their timestamps for removal
        """
        filler_instances = []
        
        for segment in transcript_segments:
            words = segment.get('words', [])
            text = segment.get('text', '').lower()
            
            # Check each word
            for word_data in words:
                word = word_data.get('word', '').lower().strip('.,!?')
                
                if word in self.fillers:
                    filler_instances.append({
                        'word': word,
                        'start': word_data.get('start', 0),
                        'end': word_data.get('end', 0),
                        'type': 'single_word'
                    })
            
            # Check for multi-word fillers
            for filler in self.fillers:
                if ' ' in filler and filler in text:
                    # Find position in segment
                    start_idx = text.find(filler)
                    if start_idx != -1:
                        # Estimate timing based on position
                        seg_duration = segment.get('end', 0) - segment.get('start', 0)
                        text_len = len(text)
                        start_ratio = start_idx / text_len
                        end_ratio = (start_idx + len(filler)) / text_len
                        
                        filler_instances.append({
                            'word': filler,
                            'start': segment['start'] + (seg_duration * start_ratio),
                            'end': segment['start'] + (seg_duration * end_ratio),
                            'type': 'phrase'
                        })
        
        return filler_instances
    
    def generate_silent_regions(self, fillers: List[Dict], padding: float = 0.05) -> List[Tuple[float, float]]:
        """
        Convert filler instances to silent regions for audio processing
        """
        regions = []
        
        for filler in fillers:
            start = max(0, filler['start'] - padding)
            end = filler['end'] + padding
            regions.append((start, end))
        
        # Merge overlapping regions
        regions.sort(key=lambda x: x[0])
        merged = []
        
        for start, end in regions:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        
        return merged


class EngagementPredictor:
    """
    Engagement Prediction Model
    Predicts view count, engagement rate, and optimal posting times
    """
    
    # Platform-specific multipliers (based on research)
    PLATFORM_MULTIPLIERS = {
        'tiktok': {'views': 1.2, 'engagement': 1.5},
        'reels': {'views': 1.0, 'engagement': 1.2},
        'shorts': {'views': 0.9, 'engagement': 1.0},
        'youtube': {'views': 0.7, 'engagement': 0.8}
    }
    
    # Optimal posting hours (UTC+7 Jakarta time)
    OPTIMAL_HOURS = {
        'weekday': [7, 8, 12, 13, 19, 20, 21],
        'weekend': [10, 11, 14, 15, 19, 20, 21, 22]
    }
    
    def __init__(self):
        pass
    
    def predict_engagement(
        self,
        virality_metrics: ViralityMetrics,
        duration: float,
        platform: str = 'tiktok'
    ) -> Dict:
        """
        Predict engagement metrics for a clip
        """
        multiplier = self.PLATFORM_MULTIPLIERS.get(platform, {'views': 1.0, 'engagement': 1.0})
        
        base_score = virality_metrics.overall_score
        
        # View prediction (relative scale 1-100, where 100 = viral potential)
        view_potential = int(base_score * 100 * multiplier['views'])
        
        # Engagement rate prediction (%)
        engagement_rate = base_score * 12 * multiplier['engagement']  # Max ~12%
        
        # Duration adjustment
        if duration <= 15:
            view_potential = int(view_potential * 1.2)
            engagement_rate *= 1.15
        elif duration > 45:
            view_potential = int(view_potential * 0.85)
            engagement_rate *= 0.9
        
        # Confidence level
        confidence = self._calculate_confidence(virality_metrics)
        
        return {
            'view_potential_score': min(100, view_potential),
            'predicted_engagement_rate': round(min(15.0, engagement_rate), 2),
            'share_likelihood': round(virality_metrics.shareability * 100, 1),
            'confidence': confidence,
            'optimal_posting_times': self._get_optimal_times(),
            'platform': platform,
            'recommendation': self._generate_recommendation(view_potential, engagement_rate)
        }
    
    def _calculate_confidence(self, metrics: ViralityMetrics) -> str:
        """Calculate prediction confidence level"""
        score = metrics.overall_score
        
        if score >= 0.75:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _get_optimal_times(self) -> List[str]:
        """Get optimal posting times in readable format"""
        from datetime import datetime
        
        is_weekend = datetime.now().weekday() >= 5
        hours = self.OPTIMAL_HOURS['weekend' if is_weekend else 'weekday']
        
        return [f"{h:02d}:00" for h in hours[:3]]  # Top 3 times
    
    def _generate_recommendation(self, view_potential: int, engagement_rate: float) -> str:
        """Generate human-readable recommendation"""
        if view_potential >= 80 and engagement_rate >= 8:
            return "🔥 VIRAL POTENTIAL - Prioritas tinggi untuk posting segera"
        elif view_potential >= 60 and engagement_rate >= 5:
            return "✨ STRONG PERFORMER - Sangat bagus untuk platform ini"
        elif view_potential >= 40 and engagement_rate >= 3:
            return "👍 GOOD CONTENT - Performa di atas rata-rata"
        else:
            return "📊 AVERAGE - Pertimbangkan untuk edit atau gabungkan dengan hook lebih kuat"


# Convenience function to get all enterprise features
def get_enterprise_analyzer(language: str = 'id') -> Dict:
    """
    Get all enterprise feature instances
    """
    return {
        'virality_scorer': EnhancedViralityScorer(language),
        'auto_reframe': SmartAutoReframe(),
        'caption_generator': AnimatedCaptionGenerator(CaptionStyle.HORMOZI),
        'filler_remover': FillerWordRemover(language),
        'engagement_predictor': EngagementPredictor()
    }
