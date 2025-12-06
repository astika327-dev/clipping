"""
Clip Generator Module
Combines audio and video analysis to generate optimal clips
"""
import os
import re
import subprocess
import time
from typing import List, Dict, Tuple
from collections import Counter
import json
from datetime import timedelta


class TimotyHookGenerator:
    """Generate punchy hook lines inspired by Timoty Ronald's delivery."""

    def __init__(self):
        self.theme_keywords = {
            'closing': {
                'keywords': [
                    'closing', 'close', 'deal', 'prospek', 'prospect', 'client',
                    'pitch', 'pitching', 'sales', 'closingan', 'closingnya'
                ],
                'pain_words': ['prospek kabur', 'ditolak klien', 'gak jadi closing']
            },
            'money': {
                'keywords': [
                    'cuan', 'omset', 'omzet', 'profit', 'untung', 'uang', 'gaji',
                    'revenue', 'closing rate', 'bonus'
                ],
                'pain_words': ['cuan bocor', 'omset mampet', 'duit ke mana']
            },
            'mindset': {
                'keywords': [
                    'mindset', 'mental', 'takut', 'percaya', 'berani', 'malu',
                    'nyali', 'fokus', 'disiplin', 'komit'
                ],
                'pain_words': ['mental tempe', 'gak pede', 'ditolak terus']
            },
            'urgency': {
                'keywords': [
                    'sekarang', 'hari ini', 'deadline', 'detik ini', 'malam ini',
                    'cepatan', 'nunda', 'kesempatan', 'chance'
                ],
                'pain_words': ['kesempatan lewat', 'delay bikin ambyar', 'ketinggalan momen']
            }
        }

        self.openers = [
            'Bro, dengerin bentar',
            'Gue kasih tau jujur',
            'Timoty selalu bilang',
            'Ini brutal banget',
            'Lu harus sadar'
        ]
        self.action_phrases = [
            'bikin prospek kebuka',
            'langsung nutup deal',
            'angkat conversion sampai 3x',
            'bikin lawan bicara diem',
            'pecahin sales mentok'
        ]
        self.commands = [
            'Catet sekarang juga',
            'Jangan tunggu minggu depan',
            'Langsung praktek hari ini',
            'Jangan kebanyakan mikir',
            'Tes di prospek berikutnya'
        ]
        self.templates = {
            'closing': [
                '{opener}! Gue bongkar kenapa {focus}. {command}.',
                '{opener}! Ini cara paling cepet biar {focus}. {command}.',
                '{opener}! Lu gagal karena {focus}. {command}.'
            ],
            'money': [
                '{opener}! {focus} itu kunci cuan. {command}.',
                '{opener}! Lu mau naikin omset? Stop {focus} terus. {command}.',
                '{opener}! {focus} bisa bikin dompet lu meledak. {command}.'
            ],
            'mindset': [
                '{opener}! Kalau {focus}, mental lu belum siap. {command}.',
                '{opener}! Timoty selalu hantam soal {focus}. {command}.',
                '{opener}! {focus} itu bedain yang sukses sama yang nyerah. {command}.'
            ],
            'urgency': [
                '{opener}! {focus}. {command}.',
                '{opener}! Lu kelamaan nunda sampe {focus}. {command}.',
                '{opener}! {focus} kalau lu masih santai. {command}.'
            ],
            'default': [
                '{opener}! {focus}. {command}.',
                '{opener}! Ini blueprint ala Timoty: {focus}. {command}.',
                '{opener}! Gue gak mau lu ulang {focus}. {command}.'
            ]
        }
        self.power_vocabulary = set(
            sum((block['keywords'] for block in self.theme_keywords.values()), [])
        )

    def generate(self, segment: Dict) -> Dict:
        """Generate hook metadata for a clip segment."""
        text = (segment.get('text') or '').strip()
        if not text:
            return None

        tokens = self._tokenize(text)
        theme, theme_score = self._detect_theme(tokens)
        focus = self._extract_focus_phrase(text, theme)
        opener = self._select(self.openers, text)
        command = self._select(self.commands, text + focus)
        action = self._select(self.action_phrases, focus)
        template_pool = self.templates.get(theme, self.templates['default'])
        template = self._select(template_pool, text + theme)
        hook_text = template.format(
            opener=opener,
            focus=self._inject_action(focus, theme, action),
            command=command,
            action=action
        )

        audio_scores = segment.get('audio', {})
        base_confidence = 0.45
        confidence = min(
            1.0,
            base_confidence +
            audio_scores.get('hook', 0) * 0.25 +
            audio_scores.get('engagement', 0) * 0.2 +
            theme_score * 0.1
        )

        return {
            'text': hook_text.strip(),
            'theme': theme,
            'confidence': round(confidence, 2),
            'power_words': self._extract_power_words(tokens),
            'source_fragment': focus
        }

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def _detect_theme(self, tokens: List[str]) -> Tuple[str, float]:
        best_theme = 'default'
        best_score = 0.0
        for theme, block in self.theme_keywords.items():
            matches = sum(1 for token in tokens if token in block['keywords'])
            normalized = matches / 4.0
            if normalized > best_score:
                best_theme = theme
                best_score = normalized
        return best_theme, min(best_score, 1.0)

    def _extract_focus_phrase(self, text: str, theme: str) -> str:
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        if not sentences:
            sentences = [text.strip()]
        theme_words = set(self.theme_keywords.get(theme, {}).get('keywords', []))
        scored = []
        for sentence in sentences:
            lower_words = re.findall(r'\b\w+\b', sentence.lower())
            score = sum(1 for word in lower_words if word in theme_words)
            scored.append((score, len(sentence), sentence))
        scored.sort(reverse=True)
        focus_sentence = scored[0][2] if scored else sentences[0]
        words = focus_sentence.split()
        return ' '.join(words[:14]).strip()

    def _inject_action(self, focus: str, theme: str, action: str) -> str:
        if theme == 'closing' and action:
            return f'{focus} biar {action}'
        return focus

    def _extract_power_words(self, tokens: List[str]) -> List[str]:
        seen = []
        for token in tokens:
            if token in self.power_vocabulary and token not in seen:
                seen.append(token)
        return seen[:5]

    def _select(self, options: List[str], seed: str) -> str:
        if not options:
            return ''
        idx = abs(hash(seed)) % len(options)
        return options[idx]



class ClipGenerator:
    def __init__(self, video_path: str, config):
        self.video_path = video_path
        self.config = config
        self.clips = []
        self.hook_generator = TimotyHookGenerator()
        
    def generate_clips(self, video_analysis: Dict, audio_analysis: Dict,
                      target_duration: str = 'all', style: str = 'balanced',
                      hook_mode: str = None) -> List[Dict]:
        """
        Generate clips based on analysis
        
        Args:
            video_analysis: Results from VideoAnalyzer
            audio_analysis: Results from AudioAnalyzer
            target_duration: 'short' (9-15s), 'medium' (18-22s), 'long' (28-32s), or 'all'
            style: 'funny', 'educational', 'dramatic', 'controversial', or 'balanced'
        """
        print("✂️ Generating clips...")

        # Store punchlines for text flash overlays
        analysis_data = audio_analysis.get('analysis', {})
        self.punchlines = analysis_data.get('punchlines', [])
        if self.punchlines:
            print(f"⚡ Punchlines available: {len(self.punchlines)} total")
        
        # Merge analyses
        segments = self._merge_analyses(video_analysis, audio_analysis)
        
        # Score and rank segments
        scored_segments = self._score_segments(segments, style)
        
        # Select best segments
        selected = self._select_clips(scored_segments, target_duration)
        
        # Generate clip metadata
        clips = self._create_clip_metadata(selected, hook_mode=hook_mode)
        
        print(f"✅ Generated {len(clips)} clips")
        
        return clips
    
    def _merge_analyses(self, video_analysis: Dict, audio_analysis: Dict) -> List[Dict]:
        """
        Merge video scenes with audio segments.
        For monologs/podcasts with few scene changes, use time-based fallback segmentation.
        """
        print("🔗 Merging video and audio analysis...")
        
        scenes = video_analysis['scenes']
        audio_segments = audio_analysis['analysis']['segment_scores']
        video_duration = video_analysis.get('duration', 0)
        
        merged = []
        
        for scene in scenes:
            # Find overlapping audio segments
            overlapping_audio = [
                seg for seg in audio_segments
                if self._segments_overlap(
                    (scene['start_time'], scene['end_time']),
                    (seg['start'], seg['end'])
                )
            ]
            
            if overlapping_audio:
                # Combine text from overlapping segments
                combined_text = ' '.join([seg['text'] for seg in overlapping_audio])
                
                # Average audio scores
                avg_audio_scores = self._average_audio_scores(overlapping_audio)
                
                merged.append({
                    'start': scene['start_time'],
                    'end': scene['end_time'],
                    'duration': scene['duration'],
                    'text': combined_text,
                    'visual': {
                        'has_faces': scene['has_faces'],
                        'face_count': scene['face_count'],
                        'has_closeup': scene['has_closeup'],
                        'motion_score': scene['motion_score'],
                        'has_high_motion': scene['has_high_motion'],
                        'visual_engagement': scene['visual_engagement']
                    },
                    'audio': avg_audio_scores
                })
        
        # Fallback: If too few scenes (monolog/podcast), add time-based segments
        if len(merged) < 3 and video_duration > 0 and audio_segments:
            print(f"⚠️  Few scenes detected ({len(merged)}). Using time-based fallback for monolog/podcast...")
            fallback_segments = self._create_time_based_segments(audio_segments, video_duration)
            merged.extend(fallback_segments)
            merged = sorted(merged, key=lambda x: x['start'])  # Sort by start time
        
        return merged
    
    def _segments_overlap(self, seg1: Tuple[float, float], seg2: Tuple[float, float]) -> bool:
        """Check if two time segments overlap"""
        return seg1[0] <= seg2[1] and seg2[0] <= seg1[1]
    
    def _create_time_based_segments(self, audio_segments: List[Dict], video_duration: float) -> List[Dict]:
        """
        Create time-based segments for monolog/podcast videos with minimal scene changes.
        Uses smart detection of pauses (silence) and audio quality to create natural breaks.
        Falls back to fixed 25-second chunks if not enough pause points.
        """
        fallback_segments = []
        
        # Detect natural pause points in audio (silence, jeda)
        pause_points = self._detect_pause_points(audio_segments)
        
        if pause_points and len(pause_points) > 2:
            # Use pause-based segmentation
            print(f"📍 Found {len(pause_points)} natural pause points in audio")
            fallback_segments = self._segment_by_pauses(audio_segments, pause_points)
        else:
            # Fall back to time-based segmentation
            fallback_segments = self._segment_by_time(audio_segments, video_duration)
        
        return fallback_segments
    
    def _detect_pause_points(self, audio_segments: List[Dict]) -> List[float]:
        """
        Detect natural pause points (silence or low engagement) in audio.
        Returns list of timestamps where pauses occur.
        """
        pause_points = []
        
        for i in range(len(audio_segments) - 1):
            current = audio_segments[i]
            next_seg = audio_segments[i + 1]
            
            # Gap between segments might indicate a pause
            gap = next_seg['start'] - current['end']
            
            # If there's a significant gap (>0.5s), it's likely a pause
            if gap > 0.5:
                pause_points.append((current['end'] + next_seg['start']) / 2)
            
            # Or if current segment has low engagement (podcast characteristic)
            current_engagement = current['scores'].get('engagement', 0.5)
            next_engagement = next_seg['scores'].get('engagement', 0.5)
            
            # Low engagement followed by higher engagement = pause point
            if current_engagement < 0.3 and next_engagement > 0.5:
                pause_points.append(current['end'])
        
        return pause_points
    
    def _segment_by_pauses(self, audio_segments: List[Dict], pause_points: List[float]) -> List[Dict]:
        """Create segments around natural pause points."""
        segments = []
        
        for i in range(len(pause_points) - 1):
            start = pause_points[i]
            end = pause_points[i + 1]
            duration = end - start
            
            # Only use segments between 10-35 seconds
            if 10 <= duration <= 35:
                overlapping_audio = [
                    seg for seg in audio_segments
                    if self._segments_overlap((start, end), (seg['start'], seg['end']))
                ]
                
                if overlapping_audio:
                    combined_text = ' '.join([seg.get('text', '') for seg in overlapping_audio])
                    avg_audio_scores = self._average_audio_scores(overlapping_audio)
                    
                    segments.append({
                        'start': start,
                        'end': end,
                        'duration': duration,
                        'text': combined_text,
                        'visual': {
                            'has_faces': True,
                            'face_count': 1,
                            'has_closeup': True,
                            'motion_score': 0.35,
                            'has_high_motion': False,
                            'visual_engagement': 0.5
                        },
                        'audio': avg_audio_scores,
                        'is_fallback': True
                    })
        
        return segments
    
    def _segment_by_time(self, audio_segments: List[Dict], video_duration: float) -> List[Dict]:
        """
        Create fixed time-based segments for monolog/podcast videos.
        Splits into 20-30 second chunks with 75% overlap for smooth transitions.
        """
        fallback_segments = []
        segment_length = 25  # 25 seconds per segment
        
        start_time = 0
        while start_time < video_duration:
            end_time = min(start_time + segment_length, video_duration)
            
            # Find audio segments that overlap
            overlapping_audio = [
                seg for seg in audio_segments
                if self._segments_overlap((start_time, end_time), (seg['start'], seg['end']))
            ]
            
            if overlapping_audio:
                combined_text = ' '.join([seg.get('text', '') for seg in overlapping_audio])
                avg_audio_scores = self._average_audio_scores(overlapping_audio)
                
                fallback_segments.append({
                    'start': start_time,
                    'end': end_time,
                    'duration': end_time - start_time,
                    'text': combined_text,
                    'visual': {
                        'has_faces': True,
                        'face_count': 1,
                        'has_closeup': True,
                        'motion_score': 0.35,
                        'has_high_motion': False,
                        'visual_engagement': 0.5
                    },
                    'audio': avg_audio_scores,
                    'is_fallback': True
                })
            
            start_time += segment_length * 0.75  # 75% overlap
        
        return fallback_segments
    
    def _average_audio_scores(self, segments: List[Dict]) -> Dict:
        """Average audio scores from multiple segments"""
        if not segments:
            return {}
        
        keys = [
            'hook', 'emotional', 'controversial', 'educational', 'entertaining',
            'engagement', 'money', 'urgency', 'mental_slap',
            'rare_topic', 'meta_topic_strength'
        ]
        averaged = {}
        
        for key in keys:
            values = [seg['scores'].get(key) for seg in segments if key in seg['scores']]
            averaged[key] = sum(values) / len(values) if values else 0
        
        meta_topics = [seg['scores'].get('meta_topic') for seg in segments if seg['scores'].get('meta_topic')]
        if meta_topics:
            averaged['meta_topic'] = Counter(meta_topics).most_common(1)[0][0]
        
        return averaged
    
    def _score_segments(self, segments: List[Dict], style: str) -> List[Dict]:
        """
        Score each segment for clip potential
        """
        print(f"📊 Scoring segments (style: {style})...")
        
        scored = []
        
        for segment in segments:
            # Calculate viral score based on style
            viral_score = self._calculate_viral_score(segment, style)
            
            # Determine category
            category = self._determine_category(segment)
            
            # Check if duration is suitable
            suitable_duration = self._check_duration_suitability(segment['duration'])
            
            scored.append({
                **segment,
                'viral_score': viral_score,
                'category': category,
                'suitable_duration': suitable_duration
            })
        
        # Sort by viral score
        scored.sort(key=lambda x: x['viral_score'], reverse=True)
        
        return scored
    
    def _calculate_viral_score(self, segment: Dict, style: str) -> float:
        """
        Calculate viral potential score (0-1)
        Enhanced for better viral detection with aggressive weighting.
        Special boost for fallback segments (monolog/podcast).
        """
        visual = segment['visual']
        audio = segment['audio']
        is_fallback = segment.get('is_fallback', False)
        
        # Fallback boost: for monolog/podcast, be more lenient with scoring
        fallback_multiplier = 1.2 if is_fallback else 1.0
        
        # Enhanced base scores with higher weights for viral indicators
        hook_strength = audio.get('hook', 0) * 0.35  # Increased from 0.30
        audio_engagement = audio.get('engagement', 0) * 0.25  # Increased from 0.15
        
        # Content value with money and urgency keywords
        content_value = (
            audio.get('emotional', 0) * 0.12 +  # Increased from 0.10
            audio.get('educational', 0) * 0.08 +
            audio.get('entertaining', 0) * 0.08 +  # Increased from 0.07
            audio.get('controversial', 0) * 0.05 +
            audio.get('money', 0) * 0.10 +
            audio.get('urgency', 0) * 0.10
        )
        
        # Visual engagement with higher priority
        visual_engagement = visual.get('visual_engagement', 0) * 0.25  # Increased from 0.20
        
        # For fallback (talking head), reduce visual penalty
        if is_fallback and visual.get('has_faces'):
            visual_engagement += 0.15  # Boost for assumed talking head
        
        # Pacing score - prefer shorter, punchier clips
        if segment['duration'] <= 15:
            pacing = 0.15  # Short clips get higher score
        elif segment['duration'] <= 25:
            pacing = 0.10
        else:
            pacing = 0.05
        
        # Style-specific bonuses (increased)
        style_bonus = 0
        if style == 'funny':
            style_bonus = audio.get('entertaining', 0) * 0.15
        elif style == 'educational':
            style_bonus = audio.get('educational', 0) * 0.15
        elif style == 'dramatic':
            style_bonus = audio.get('emotional', 0) * 0.15
        elif style == 'controversial':
            style_bonus = audio.get('controversial', 0) * 0.15
        elif style == 'balanced':
            # For balanced, use average of all content scores
            style_bonus = (audio.get('entertaining', 0) + audio.get('educational', 0) + 
                          audio.get('emotional', 0)) / 3 * 0.10
        
        # Visual bonuses - more aggressive
        visual_bonus = 0
        if visual.get('has_closeup'):
            visual_bonus += 0.08  # Increased from 0.05
        if visual.get('has_high_motion'):
            visual_bonus += 0.08  # Increased from 0.05
        if visual.get('has_faces'):
            visual_bonus += 0.05  # Added face detection bonus
        
        # Check for questions (high engagement)
        if segment.get('text') and '?' in segment['text']:
            audio_engagement += 0.05
        
        # Check for numbers/stats (credibility boost)
        if segment.get('text'):
            import re
            if re.search(r'\d+', segment['text']):
                content_value += 0.05
        
        relatability_bonus = (
            audio.get('mental_slap', 0) * 0.2 +
            audio.get('meta_topic_strength', 0) * 0.15
        )

        rare_topic_penalty = audio.get('rare_topic', 0) * 0.2

        total_score = (
            hook_strength +
            content_value +
            visual_engagement +
            audio_engagement +
            pacing +
            style_bonus +
            visual_bonus +
            relatability_bonus -
            rare_topic_penalty
        )
        
        # Apply fallback multiplier to boost monolog/podcast scores slightly
        total_score *= fallback_multiplier
        
        return max(0.0, min(total_score, 1.0))
    
    def _determine_category(self, segment: Dict) -> str:
        """Determine the primary category of the segment"""
        audio = segment['audio']
        
        categories = {
            'educational': audio.get('educational', 0),
            'entertaining': audio.get('entertaining', 0),
            'emotional': audio.get('emotional', 0),
            'controversial': audio.get('controversial', 0)
        }
        
        return max(categories.items(), key=lambda x: x[1])[0]
    
    def _check_duration_suitability(self, duration: float) -> str:
        """Check which duration category this segment fits"""
        if 9 <= duration <= 15:
            return 'short'
        elif 18 <= duration <= 22:
            return 'medium'
        elif 28 <= duration <= 32:
            return 'long'
        else:
            return 'custom'
    
    def _select_clips(self, scored_segments: List[Dict], target_duration: str) -> List[Dict]:
        """Select clip segments quickly while guaranteeing minimum output."""
        selected = []

        if target_duration != 'all':
            candidates = [s for s in scored_segments if s['suitable_duration'] == target_duration]
        else:
            candidates = [s for s in scored_segments if s['suitable_duration'] != 'custom']

        if not candidates:
            candidates = self._adjust_segment_durations(scored_segments, target_duration)

        max_clips = max(1, getattr(self.config, 'MAX_CLIPS_PER_VIDEO', 15))
        min_required = min(max_clips, max(1, getattr(self.config, 'MIN_CLIP_OUTPUT', 10)))
        target_goal = min(max_clips, max(min_required, getattr(self.config, 'TARGET_CLIP_COUNT', min_required)))

        base_threshold = getattr(self.config, 'MIN_VIRAL_SCORE', 0.5)
        relaxed_threshold = max(getattr(self.config, 'RELAXED_VIRAL_SCORE', base_threshold - 0.1), 0.0)
        fallback_threshold = max(getattr(self.config, 'FALLBACK_VIRAL_SCORE', relaxed_threshold - 0.1), 0.0)

        seen_keys = set()

        def pick(threshold: float, limit: int) -> None:
            limit = min(limit, max_clips)
            if len(selected) >= limit:
                return
            for segment in candidates:
                if len(selected) >= limit:
                    break
                key = (round(segment['start'], 2), round(segment['end'], 2))
                if key in seen_keys:
                    continue
                if segment['viral_score'] < threshold:
                    continue
                if not self._is_distinct_segment(segment, selected):
                    continue
                selected.append(segment)
                seen_keys.add(key)

        for threshold, limit in (
            (base_threshold, target_goal),
            (relaxed_threshold, target_goal),
            (relaxed_threshold, max_clips),
            (fallback_threshold, max_clips),
        ):
            pick(threshold, limit)
            if len(selected) >= max_clips:
                break

        if len(selected) < min_required and candidates:
            fallback_sorted = sorted(candidates, key=lambda item: item['viral_score'], reverse=True)
            for segment in fallback_sorted:
                if len(selected) >= min(max_clips, min_required):
                    break
                key = (round(segment['start'], 2), round(segment['end'], 2))
                if key in seen_keys:
                    continue
                if not self._is_distinct_segment(segment, selected):
                    continue
                selected.append(segment)
                seen_keys.add(key)

        return selected
    
    def _adjust_segment_durations(self, segments: List[Dict], target: str) -> List[Dict]:
        """
        Try to adjust segment durations to fit target
        """
        # This is a simplified version - could be more sophisticated
        adjusted = []
        
        target_ranges = {
            'short': (9, 15),
            'medium': (18, 22),
            'long': (28, 32)
        }
        
        if target == 'all':
            return segments
        
        min_dur, max_dur = target_ranges.get(target, (9, 35))
        
        for segment in segments:
            duration = segment['duration']
            
            # If too long, we could trim it
            if duration > max_dur:
                # Trim from the end
                segment['end'] = segment['start'] + max_dur
                segment['duration'] = max_dur
                segment['suitable_duration'] = target
                adjusted.append(segment)
            
            # If too short, we could extend it (if there's content)
            elif duration < min_dur and duration > min_dur * 0.7:
                # Extend slightly
                segment['end'] = segment['start'] + min_dur
                segment['duration'] = min_dur
                segment['suitable_duration'] = target
                adjusted.append(segment)
        
        return adjusted

    def _is_distinct_segment(self, candidate: Dict, selected: List[Dict]) -> bool:
        """Prevent near-duplicate clips by enforcing overlap and spacing rules."""
        if not selected:
            return True

        min_gap = max(0.0, getattr(self.config, 'MIN_CLIP_GAP_SECONDS', 3.0))
        max_overlap = max(0.0, getattr(self.config, 'MAX_CLIP_OVERLAP_RATIO', 0.6))

        for existing in selected:
            overlap = self._calculate_overlap_ratio(existing, candidate)
            if overlap >= max_overlap:
                return False

            start_gap = abs(candidate['start'] - existing['start'])
            end_gap = abs(candidate['end'] - existing['end'])
            if start_gap < min_gap and end_gap < min_gap:
                return False

        return True

    @staticmethod
    def _calculate_overlap_ratio(seg_a: Dict, seg_b: Dict) -> float:
        """Measure overlap relative to the shorter clip to detect duplicates."""
        start = max(seg_a['start'], seg_b['start'])
        end = min(seg_a['end'], seg_b['end'])
        if end <= start:
            return 0.0

        overlap = end - start
        shortest = max(0.01, min(seg_a['duration'], seg_b['duration']))
        return overlap / shortest
    
    def _create_clip_metadata(self, segments: List[Dict], hook_mode: str = None) -> List[Dict]:
        """
        Create metadata for each clip
        """
        clips = []
        
        for idx, segment in enumerate(segments):
            # Generate title
            title = self._generate_title(segment)
            
            # Determine viral level
            viral_level = self._get_viral_level(segment['viral_score'])
            
            # Generate reason
            reason = self._generate_reason(segment)
            
            clip_payload = {
                'id': idx + 1,
                'filename': f'clip_{idx + 1:03d}.mp4',
                'title': title,
                'start_time': self._format_timestamp(segment['start']),
                'end_time': self._format_timestamp(segment['end']),
                'start_seconds': segment['start'],
                'end_seconds': segment['end'],
                'duration': segment['duration'],
                'viral_score': viral_level,
                'viral_score_numeric': round(segment['viral_score'], 2),
                'reason': reason,
                'category': segment['category'],
                'transcript': segment['text'][:200] + '...' if len(segment['text']) > 200 else segment['text']
            }

            if hook_mode == 'timoty':
                hook_detail = self.hook_generator.generate(segment)
                if hook_detail:
                    clip_payload['timoty_hook'] = hook_detail
            clips.append(clip_payload)
        
        return clips

    def attach_captions(self, clips: List[Dict], transcript_segments: List[Dict]) -> None:
        """Attach caption metadata to clips based on transcript segments."""
        if not transcript_segments:
            return

        for clip in clips:
            entries = self._build_caption_entries(clip, transcript_segments)
            if not entries:
                continue
            clip['captions'] = entries
            clip['caption_file'] = clip['filename'].rsplit('.', 1)[0] + '.srt'
            clip['caption_preview'] = ' / '.join(entry['text'] for entry in entries[:2])
    
    def _generate_title(self, segment: Dict) -> str:
        """Generate a catchy title for the clip"""
        category = segment['category']
        text = segment['text'][:50]
        
        # Extract key phrase
        words = text.split()
        if len(words) > 5:
            key_phrase = ' '.join(words[:5])
        else:
            key_phrase = text
        
        return f"{key_phrase}..."
    
    def _get_viral_level(self, score: float) -> str:
        """Convert numeric score to level"""
        if score >= 0.75:
            return 'Tinggi'
        elif score >= 0.5:
            return 'Sedang'
        else:
            return 'Rendah'
    
    def _generate_reason(self, segment: Dict) -> str:
        """Generate explanation for viral score"""
        reasons = []
        
        audio = segment['audio']
        visual = segment['visual']
        
        if audio.get('hook', 0) > 0.5:
            reasons.append('hook kuat')
        
        if audio.get('emotional', 0) > 0.5:
            reasons.append('konten emosional')
        
        if audio.get('controversial', 0) > 0.5:
            reasons.append('opini kontroversial')
        
        if visual.get('has_closeup'):
            reasons.append('close-up speaker')
        
        if visual.get('has_high_motion'):
            reasons.append('visual dinamis')
        
        if not reasons:
            reasons.append('konten informatif')
        
        return ' + '.join(reasons).capitalize()
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        return str(timedelta(seconds=int(seconds)))
    
    def export_clip(self, clip: Dict, output_dir: str) -> str:
        """
        Export a single clip using FFmpeg with 16:9 aspect ratio and optional hook overlay
        """
        output_path = os.path.join(output_dir, clip['filename'])
        
        # Build video filter for 16:9 aspect ratio
        # Scale and pad/crop to 1920x1080 (16:9)
        video_filters = [
            f"scale=w={self.config.TARGET_WIDTH}:h={self.config.TARGET_HEIGHT}:force_original_aspect_ratio=decrease",
            f"pad={self.config.TARGET_WIDTH}:{self.config.TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
        ]
        
        # FFmpeg command with filters
        composite_filter = ','.join(video_filters)

        cmd = [
            'ffmpeg',
            '-i', self.video_path,
            '-ss', str(clip['start_seconds']),
            '-t', str(clip['duration']),
            '-vf', composite_filter
        ]
        
        # Add encoding parameters
        cmd.extend([
            '-c:v', self.config.VIDEO_CODEC,
            '-b:v', self.config.VIDEO_BITRATE,
            '-c:a', self.config.AUDIO_CODEC,
            '-b:a', self.config.AUDIO_BITRATE,
            '-preset', 'fast',  # Faster encoding
            '-y',  # Overwrite output file
            output_path
        ])
        
        # Run FFmpeg
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Error exporting clip: {e}")
            print(f"   FFmpeg stderr: {e.stderr}")
            return None
    
    def export_all_clips(self, clips: List[Dict], output_dir: str) -> List[str]:
        """
        Export all clips
        """
        print(f"💾 Exporting {len(clips)} clips...")
        
        exported = []
        delay = getattr(self.config, 'EXPORT_THROTTLE_SECONDS', 0)
        
        for idx, clip in enumerate(clips):
            print(f"  Exporting clip {idx + 1}/{len(clips)}: {clip['filename']}")
            output_path = self.export_clip(clip, output_dir)
            
            if output_path:
                exported.append(output_path)
                if clip.get('captions'):
                    self._write_caption_file(clip, output_dir)
            if delay and delay > 0 and idx < len(clips) - 1:
                time.sleep(delay)
        
        print(f"✅ Exported {len(exported)} clips successfully")
        
        return exported

    def _build_caption_entries(self, clip: Dict, segments: List[Dict]) -> List[Dict]:
        clip_start = clip['start_seconds']
        clip_end = clip['end_seconds']
        entries = []
        for segment in segments:
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', 0)
            if seg_end <= clip_start or seg_start >= clip_end:
                continue
            relative_start = max(seg_start, clip_start) - clip_start
            relative_end = min(seg_end, clip_end) - clip_start
            if relative_end - relative_start < 0.15:
                continue
            text = (segment.get('text') or '').strip()
            if not text:
                continue
            entries.append({
                'index': len(entries) + 1,
                'start': self._format_srt_timestamp(relative_start),
                'end': self._format_srt_timestamp(relative_end),
                'text': text
            })
        return entries

    def _format_srt_timestamp(self, seconds: float) -> str:
        total_ms = max(0, int(round(seconds * 1000)))
        hours = total_ms // 3_600_000
        minutes = (total_ms % 3_600_000) // 60_000
        secs = (total_ms % 60_000) // 1000
        millis = total_ms % 1000
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def _write_caption_file(self, clip: Dict, output_dir: str) -> None:
        caption_path = os.path.join(output_dir, clip['caption_file'])
        with open(caption_path, 'w', encoding='utf-8') as caption_file:
            for entry in clip['captions']:
                caption_file.write(f"{entry['index']}\n")
                caption_file.write(f"{entry['start']} --> {entry['end']}\n")
                caption_file.write(f"{entry['text']}\n\n")

    def _build_text_flashes(self, clip: Dict) -> List[Dict]:
        """Determine punchy text overlay moments (FAKTOR 11)."""
        if not getattr(self.config, 'TEXT_FLASH_ENABLED', True):
            return []

        vocab = getattr(self.config, 'TEXT_FLASH_VOCAB', [])
        max_flashes = getattr(self.config, 'MAX_TEXT_FLASH_PER_CLIP', 3)
        duration = clip['duration']
        flashes = []

        candidates = []
        for punch in self.punchlines:
            start = punch.get('start', 0)
            end = punch.get('end', 0)
            text = (punch.get('text') or '').strip()
            score = punch.get('score', 0)
            if not text:
                continue
            abs_start = start - clip['start_seconds']
            abs_end = end - clip['start_seconds']
            if abs_end <= 0 or abs_start >= duration:
                continue
            center = max(0, min(duration, (abs_start + abs_end) / 2))
            overlay_text = self._pick_flash_word(text, vocab)
            candidates.append({
                'center': center,
                'text': overlay_text or text[:12].upper(),
                'score': score
            })

        if candidates:
            candidates.sort(key=lambda x: x['score'], reverse=True)
            used_times = []
            flash_duration = getattr(self.config, 'TEXT_FLASH_DURATION', 0.8)
            half_window = flash_duration / 2
            for candidate in candidates:
                if len(flashes) >= max_flashes:
                    break
                if any(abs(candidate['center'] - used) < flash_duration for used in used_times):
                    continue
                flashes.append({
                    'start': max(0, candidate['center'] - half_window),
                    'end': min(duration, candidate['center'] + half_window),
                    'text': candidate['text']
                })
                used_times.append(candidate['center'])

        return flashes

    def _pick_flash_word(self, punch_text: str, vocab: List[str]) -> str:
        """Choose the most relevant flash word for a punchline."""
        if not punch_text:
            return ''
        lowered = punch_text.lower()
        for word in vocab:
            if word.lower() in lowered:
                return word.upper()
        if len(punch_text.split()) <= 3:
            return punch_text.upper()
        for keyword in getattr(self.config, 'MENTAL_SLAP_KEYWORDS', []):
            if keyword.lower() in lowered:
                return keyword.upper()
        return punch_text.split()[0].upper()
