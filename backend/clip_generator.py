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
    def __init__(self, video_path: str, config, resolution: str = None):
        self.video_path = video_path
        self.config = config
        self.clips = []
        self.hook_generator = TimotyHookGenerator()
        
        # Set resolution from preset or use default
        self.resolution = resolution or getattr(config, 'DEFAULT_RESOLUTION', '1080p')
        resolution_presets = getattr(config, 'RESOLUTION_PRESETS', {
            '720p': {'width': 1280, 'height': 720, 'bitrate': '1M'},
            '1080p': {'width': 1920, 'height': 1080, 'bitrate': '2M'}
        })
        
        preset = resolution_presets.get(self.resolution, resolution_presets.get('1080p'))
        self.target_width = preset['width']
        self.target_height = preset['height']
        self.target_bitrate = preset['bitrate']
        print(f"📐 Resolution set to: {self.resolution} ({self.target_width}x{self.target_height}, {self.target_bitrate})")
        
    def generate_clips(self, video_analysis: Dict, audio_analysis: Dict,
                      target_duration: str = 'all', style: str = 'balanced',
                      hook_mode: str = None) -> List[Dict]:
        """
        Generate clips based on analysis
        GUARANTEED to return at least FORCED_MIN_CLIP_OUTPUT clips.
        
        Args:
            video_analysis: Results from VideoAnalyzer
            audio_analysis: Results from AudioAnalyzer
            target_duration: 'short' (9-15s), 'medium' (18-22s), 'long' (28-32s), 'extended' (40-50s), or 'all'
            style: 'funny', 'educational', 'dramatic', 'controversial', or 'balanced'
        """
        print("✂️ Generating clips...")
        print(f"   Target duration: {target_duration}, Style: {style}")

        # Store punchlines for text flash overlays
        analysis_data = audio_analysis.get('analysis', {})
        self.punchlines = analysis_data.get('punchlines', [])
        if self.punchlines:
            print(f"⚡ Punchlines available: {len(self.punchlines)} total")
        
        # Get audio segments count for debugging
        audio_segments = analysis_data.get('segment_scores', [])
        print(f"📊 Audio segments available: {len(audio_segments)}")
        
        # Merge analyses
        segments = self._merge_analyses(video_analysis, audio_analysis)
        
        if not segments:
            print("⚠️ WARNING: No segments after merge! Creating emergency segments...")
            segments = self._create_last_resort_segments(video_analysis, audio_analysis)
        
        # Score and rank segments
        scored_segments = self._score_segments(segments, style)
        print(f"📊 Scored segments: {len(scored_segments)}")
        
        # CRITICAL SAFETY: If scoring returned empty, create emergency segments NOW
        if not scored_segments:
            print("🚨 CRITICAL: Scoring returned 0 segments! Creating emergency segments...")
            emergency_segs = self._create_last_resort_segments(video_analysis, audio_analysis)
            scored_segments = self._score_segments(emergency_segs, style)
            if not scored_segments:
                # Absolute last resort: return unscored emergency segments
                print("🆘 ABSOLUTE EMERGENCY: Using unscored emergency segments")
                for seg in emergency_segs[:10]:  # Take first 10
                    seg['viral_score'] = 0.4
                    seg['category'] = 'educational'
                    seg['suitable_duration'] = self._check_duration_suitability(seg['duration'])
                scored_segments = emergency_segs[:10]
        
        # Debug: Show top 5 scores
        if scored_segments:
            top_scores = [s['viral_score'] for s in scored_segments[:5]]
            print(f"   Top 5 viral scores: {[round(s, 2) for s in top_scores]}")
        
        # Select best segments
        selected = self._select_clips(scored_segments, target_duration)
        print(f"📊 Selected segments: {len(selected)}")
        
        # GUARANTEE: If still 0, force create from any available data
        forced_min = max(1, getattr(self.config, 'FORCED_MIN_CLIP_OUTPUT', 3))
        if len(selected) < forced_min:
            print(f"⚠️ Only {len(selected)} clips, need at least {forced_min}. Forcing creation...")
            selected = self._guarantee_minimum_clips(selected, scored_segments, video_analysis, audio_analysis, forced_min)
        
        # CONTEXT SNAPPING: Adjust clip boundaries to align with sentence/speech breaks
        if audio_segments:
            selected = self._snap_to_context_boundaries(selected, audio_segments)

        # ENTERPRISE FEATURE: Smart Narrative Stitching
        # Merge close segments to create longer, richer narrative arcs (Podcast style)
        if target_duration in ['long', 'extended', 'all']:
             selected = self._smart_stitch_segments(selected, audio_segments, max_gap=8.0)
        
        # ENTERPRISE FEATURE: Start/End Polish
        # Trim weak semantic connectors for professional impact
        selected = self._polish_clip_boundaries(selected)

        
        # Generate clip metadata
        clips = self._create_clip_metadata(selected, hook_mode=hook_mode)
        
        print(f"✅ Generated {len(clips)} clips")
        
        # FINAL SAFETY CHECK
        if len(clips) == 0:
            print("🚨 CRITICAL: Still 0 clips! Creating absolute fallback...")
            clips = self._create_absolute_fallback_clips(video_analysis, audio_analysis)
        
        return clips
    
    def _create_last_resort_segments(self, video_analysis: Dict, audio_analysis: Dict) -> List[Dict]:
        """Create segments when everything else fails - uses video duration directly."""
        video_duration = (
            video_analysis.get('duration') or
            video_analysis.get('metadata', {}).get('duration', 0) or
            0
        )
        
        # Try to get duration from audio if video duration is 0
        audio_segments = audio_analysis.get('analysis', {}).get('segment_scores', [])
        if video_duration <= 0 and audio_segments:
            video_duration = max((seg.get('end', 0) for seg in audio_segments), default=60)
        
        # If still 0, assume 60 seconds minimum
        if video_duration <= 0:
            video_duration = 60
            print(f"⚠️ Could not determine video duration. Using default: {video_duration}s")
        
        print(f"🆘 Creating last resort segments for {video_duration:.1f}s video")
        
        segments = []
        segment_lengths = [15, 20, 25, 45]  # Various lengths including extended for better context
        
        for length in segment_lengths:
            start = 0
            while start + length <= video_duration + 5:
                end = min(start + length, video_duration)
                if end - start >= 20:  # Minimum 20 seconds for podcasts

                    segments.append({
                        'start': start,
                        'end': end,
                        'duration': end - start,
                        'text': f'Segment {start:.0f}s - {end:.0f}s',
                        'visual': {
                            'has_faces': True, 'face_count': 1, 'has_closeup': True,
                            'motion_score': 0.4, 'has_high_motion': False, 'visual_engagement': 0.5
                        },
                        'audio': {
                            'hook': 0.3, 'engagement': 0.4, 'educational': 0.3,
                            'emotional': 0.2, 'entertaining': 0.2, 'money': 0.1,
                            'urgency': 0.1, 'mental_slap': 0.1, 'meta_topic_strength': 0.1,
                            'controversial': 0.1, 'rare_topic': 0
                        },
                        'is_fallback': True,
                        'is_last_resort': True
                    })
                start += length * 0.6
        
        print(f"🆘 Created {len(segments)} last resort segments")
        return segments
    
    def _guarantee_minimum_clips(self, selected: List[Dict], scored: List[Dict], 
                                  video_analysis: Dict, audio_analysis: Dict, 
                                  min_count: int) -> List[Dict]:
        """Guarantee we have at least min_count clips by any means necessary."""
        if len(selected) >= min_count:
            return selected
        
        result = list(selected)
        seen_keys = set((round(s['start'], 2), round(s['end'], 2)) for s in result)
        
        # Step 1: Try to add from scored segments (ignore thresholds)
        for seg in scored:
            if len(result) >= min_count:
                break
            key = (round(seg['start'], 2), round(seg['end'], 2))
            if key in seen_keys:
                continue
            # Only check for severe overlap
            is_ok = True
            for existing in result:
                if self._calculate_overlap_ratio(existing, seg) > 0.85:
                    is_ok = False
                    break
            if is_ok:
                result.append(seg)
                seen_keys.add(key)
        
        # Step 2: If still not enough, create new segments
        if len(result) < min_count:
            print(f"⚠️ Still only {len(result)} clips. Creating additional segments...")
            extra_segments = self._create_last_resort_segments(video_analysis, audio_analysis)
            
            # Score and add them
            for seg in extra_segments:
                if len(result) >= min_count:
                    break
                key = (round(seg['start'], 2), round(seg['end'], 2))
                if key in seen_keys:
                    continue
                # Check overlap
                is_ok = True
                for existing in result:
                    if self._calculate_overlap_ratio(existing, seg) > 0.85:
                        is_ok = False
                        break
                if is_ok:
                    # Add required fields
                    seg['viral_score'] = 0.3
                    seg['category'] = 'educational'
                    seg['suitable_duration'] = self._check_duration_suitability(seg['duration'])
                    result.append(seg)
                    seen_keys.add(key)
        
        print(f"✅ Guaranteed {len(result)} clips")
        return result
    
    def _create_absolute_fallback_clips(self, video_analysis: Dict, audio_analysis: Dict) -> List[Dict]:
        """ABSOLUTE LAST RESORT: Create clips even if everything else failed."""
        print("🚨 ABSOLUTE FALLBACK: Creating emergency clips...")
        
        video_duration = (
            video_analysis.get('duration') or
            video_analysis.get('metadata', {}).get('duration', 0) or
            60  # Default 60 seconds
        )
        
        # Create 3 simple clips evenly spaced
        clips = []
        clip_length = min(20, video_duration / 3)  # 20 seconds or 1/3 of video
        
        for i in range(3):
            start = i * (video_duration / 3)
            end = min(start + clip_length, video_duration)
            
            if end - start >= 5:  # At least 5 seconds
                clips.append({
                    'id': i + 1,
                    'filename': f'clip_{i + 1:03d}.mp4',
                    'title': f'Clip {i + 1}',
                    'start_time': self._format_timestamp(start),
                    'end_time': self._format_timestamp(end),
                    'start_seconds': start,
                    'end_seconds': end,
                    'duration': end - start,
                    'viral_score': 'Rendah',
                    'viral_score_numeric': 0.25,
                    'reason': 'Auto-generated fallback',
                    'category': 'educational',
                    'transcript': f'Segment dari {start:.0f}s sampai {end:.0f}s'
                })
        
        print(f"🚨 Created {len(clips)} absolute fallback clips")
        return clips
    
    def _merge_analyses(self, video_analysis: Dict, audio_analysis: Dict) -> List[Dict]:
        """
        Merge video scenes with audio segments.
        For monologs/podcasts with few scene changes, use time-based fallback segmentation.
        GUARANTEED to return segments if audio_segments exist.
        """
        print("🔗 Merging video and audio analysis...")
        
        scenes = video_analysis.get('scenes', [])
        audio_segments = audio_analysis.get('analysis', {}).get('segment_scores', [])
        video_duration = (
            video_analysis.get('duration') or
            video_analysis.get('metadata', {}).get('duration', 0) or
            0
        )
        
        # Fallback: estimate duration from audio segments if missing
        if video_duration <= 0 and audio_segments:
            video_duration = max(seg.get('end', 0) for seg in audio_segments)
            print(f"📏 Estimated video duration from audio: {video_duration:.1f}s")
        
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
                combined_text = ' '.join([seg.get('text', '') for seg in overlapping_audio])
                
                # Average audio scores
                avg_audio_scores = self._average_audio_scores(overlapping_audio)
                
                merged.append({
                    'start': scene['start_time'],
                    'end': scene['end_time'],
                    'duration': scene['duration'],
                    'text': combined_text,
                    'visual': {
                        'has_faces': scene.get('has_faces', True),
                        'face_count': scene.get('face_count', 1),
                        'has_closeup': scene.get('has_closeup', True),
                        'motion_score': scene.get('motion_score', 0.3),
                        'has_high_motion': scene.get('has_high_motion', False),
                        'visual_engagement': scene.get('visual_engagement', 0.5),
                        'is_talking': scene.get('is_talking', True)  # Use DL result or default True
                    },
                    'speaker_left_ratio': scene.get('speaker_left_ratio', 0),
                    'speaker_right_ratio': scene.get('speaker_right_ratio', 0),
                    'is_conversation': scene.get('is_conversation', False),
                    'dl_speaker_analysis': scene.get('dl_speaker_analysis', {}),
                    'audio': avg_audio_scores
                })
        
        print(f"📊 Scene-based segments: {len(merged)}")
        
        # ALWAYS create fallback segments for monolog/podcast (few or no scenes)
        # This is the key fix - we need segments even when scenes are empty
        if video_duration > 0 and audio_segments:
            if len(merged) < 5:  # Always add fallback if fewer than 5 scene segments
                print(f"⚠️  Few scenes detected ({len(merged)}). Creating time-based fallback for monolog/podcast...")
                fallback_segments = self._create_time_based_segments(audio_segments, video_duration)
                print(f"📊 Fallback segments created: {len(fallback_segments)}")
                
                # Add fallback segments that don't overlap too much with existing
                for fb_seg in fallback_segments:
                    is_unique = True
                    for existing in merged:
                        overlap = self._calculate_overlap_ratio(existing, fb_seg)
                        if overlap > 0.5:
                            is_unique = False
                            break
                    if is_unique:
                        merged.append(fb_seg)
                
                merged = sorted(merged, key=lambda x: x['start'])
        
        # LAST RESORT: If still no segments, create from raw audio segments directly
        if not merged and audio_segments:
            print("🆘 No segments found. Creating emergency segments from audio directly...")
            merged = self._create_emergency_segments(audio_segments, video_duration)
            
        # REFINEMENT: If we have detailed speaker timeline, refine segments based on turns
        # This is key for 2-person podcasts to split "Q&A" or "Dialogue" correctly
        merged = self._refine_segments_with_speaker_turns(merged, scenes)
        
        print(f"📊 Total merged segments: {len(merged)}")
        return merged

    def _refine_segments_with_speaker_turns(self, segments: List[Dict], scenes: List[Dict]) -> List[Dict]:
        """
        Refine segments by splitting them at speaker transitions (turns).
        Uses the 'speaker_timeline' from AdvancedVideoAnalyzer.
        """
        if not segments or not scenes:
            return segments
            
        print("   👥 Refining segments based on speaker turns...")
        refined = []
        
        # Helper to find scene for a segment
        def get_scene_for_segment(seg):
            mid = (seg['start'] + seg['end']) / 2
            for sc in scenes:
                if sc['start_time'] <= mid <= sc['end_time']:
                    return sc
            return None
        
        for seg in segments:
            scene = get_scene_for_segment(seg)
            timeline = scene.get('dl_speaker_analysis', {}).get('timeline', []) if scene else []
            
            if not timeline or len(timeline) < 2:
                refined.append(seg)
                continue
            
            # Helper to check if a timestamp falls in this segment
            seg_start = seg['start']
            seg_end = seg['end']
            
            # Get valid timeline points for this segment
            valid_points = [p for p in timeline if seg_start <= p['timestamp'] <= seg_end]
            
            if not valid_points:
                refined.append(seg)
                continue
                
            # Detect turns: Left (Active) vs Right (Active)
            # We look for sustained blocks of one speaker
            transitions = []
            
            # Smooth out state using a sliding window? 
            # Simple approach: Find change in dominant speaker
            current_speaker = None # 'left', 'right', 'both', 'none'
            last_switch_time = seg_start
            
            for point in valid_points:
                ts = point['timestamp']
                
                # Determine state at this point
                state = 'none'
                if point.get('active_left') and point.get('active_right'):
                    state = 'both'
                elif point.get('active_left'):
                    state = 'left'
                elif point.get('active_right'):
                    state = 'right'
                
                if state == 'none': continue
                
                if current_speaker is None:
                    current_speaker = state
                    last_switch_time = ts
                elif state != current_speaker and state != 'both': # 'both' maintains current context usually
                    # Potential switch found
                    # Only register if duration since last switch is meaningful (> 10s)
                    if ts - last_switch_time > 10.0:
                        transitions.append(ts)
                        current_speaker = state
                        last_switch_time = ts
            
            if not transitions:
                refined.append(seg)
                continue
            
            # Split segment at transitions
            current_start = seg_start
            print(f"      ✂️ Splitting segment {seg_start:.1f}-{seg_end:.1f} at speaker turns: {[round(t,1) for t in transitions]}")
            
            # Split text? We can't easily split text without re-aligning words. 
            # So we duplicate the text/audio metadata but adjust times. 
            # Ideally we would re-fetch text for the new time range, but we don't have that granularity easily.
            # Best effort: Just adjust times and hope audio alignment works later or is permissive.
            # Actually, `clip_generator` downstream uses `start`/`end` to strip audio/video. 
            # The text in metadata is mostly for analysis/title.
            
            split_points = transitions + [seg_end]
            
            for split_ts in split_points:
                if split_ts - current_start < 15.0: # Ignore slivers < 15s (keep context)
                    continue
                    
                new_seg = seg.copy()
                new_seg['start'] = current_start
                new_seg['end'] = split_ts
                new_seg['duration'] = split_ts - current_start
                new_seg['split_by_turn'] = True
                new_seg['text'] = f"[Speaker Turn] {seg.get('text', '')}" # Marker
                refined.append(new_seg)
                current_start = split_ts
                
        return refined
    
    def _snap_to_context_boundaries(self, segments: List[Dict], audio_segments: List[Dict]) -> List[Dict]:
        """
        Intelligently adjust segment boundaries like a skilled editor with high IQ/EQ.
        - Aligns cuts with natural sentence/speech breaks
        - Ensures clips contain complete ideas
        - Prevents cutting mid-thought for coherent context
        - Detects conclusion/transition phrases for better endings
        """
        if not audio_segments:
            return segments
        
        # === ENHANCED BOUNDARY DETECTION ===
        # Transition words that indicate a NEW topic starting (good start points)
        transition_starters = {
            # Indonesian
            'jadi', 'nah', 'oke', 'terus', 'dan', 'tapi', 'kalau', 'pertama',
            'kedua', 'ketiga', 'selanjutnya', 'kemudian', 'sekarang', 'gini',
            'begini', 'intinya', 'poinnya', 'maksudnya', 'artinya', 'misalnya',
            'contohnya', 'faktanya', 'sebenarnya', 'sebenernya', 'padahal',
            'sedangkan', 'namun', 'akan', 'tetapi', 'bahkan', 'oleh',
            # English
            'so', 'but', 'and', 'then', 'if', 'now', 'first', 'second', 'third',
            'next', 'finally', 'basically', 'actually', 'however', 'therefore',
            'moreover', 'furthermore', 'meanwhile', 'although', 'because', 'since'
        }
        
        # Conclusion phrases that indicate topic ENDING (good end points)
        conclusion_indicators = [
            # Indonesian conclusions
            'jadi intinya', 'jadi kesimpulannya', 'intinya adalah', 'poinnya adalah',
            'yang penting', 'yang paling penting', 'kuncinya adalah', 'rahasianya',
            'itulah kenapa', 'itulah mengapa', 'makanya', 'mangkanya', 'oleh karena itu',
            'karena itu', 'satu hal yang', 'hal yang paling', 'ingat ya', 'ingat baik-baik',
            'catat ya', 'catet ya', 'simpan ini', 'ini kuncinya', 'ini rahasianya',
            # English conclusions
            'so basically', 'the point is', 'the key is', 'the secret is', 'that\'s why',
            'remember this', 'keep in mind', 'bottom line', 'in conclusion', 'to summarize'
        ]
        
        # Build a list of natural break points with quality scores
        # Each audio segment represents a transcribed phrase/sentence
        break_point_data = []
        for seg in audio_segments:
            text = (seg.get('text') or '').strip()
            text_lower = text.lower()
            
            # Start points - prefer starts of sentences
            start_quality = 0.5
            if text and len(text) > 0:
                first_word = text.split()[0].lower() if text.split() else ''
                first_two_words = ' '.join(text.split()[:2]).lower() if len(text.split()) >= 2 else ''
                
                # Better quality for transition starters
                if first_word in transition_starters:
                    start_quality = 0.95  # Excellent start point
                elif first_two_words.startswith(tuple(transition_starters)):
                    start_quality = 0.9
                elif first_word and first_word[0].isupper():
                    start_quality = 0.8
            break_point_data.append({'time': seg.get('start', 0), 'type': 'start', 'quality': start_quality})
            
            # End points - prefer ends of sentences and conclusions
            end_quality = 0.5
            if text:
                # Check for conclusion phrases (highest priority)
                has_conclusion = any(phrase in text_lower for phrase in conclusion_indicators)
                if has_conclusion:
                    end_quality = 1.0  # Perfect end point - conclusion detected
                elif text.rstrip()[-1:] in '.!?':
                    end_quality = 0.9  # Great end point - sentence complete
                elif text.rstrip()[-1:] == ',':
                    end_quality = 0.6  # Acceptable pause
            break_point_data.append({'time': seg.get('end', 0), 'type': 'end', 'quality': end_quality, 'has_conclusion': has_conclusion if text else False})
        
        # Sort by time and deduplicate
        break_point_data.sort(key=lambda x: x['time'])
        
        # Create lookup for quick access
        break_points_dict = {}
        for bp in break_point_data:
            t = round(bp['time'], 2)
            if t not in break_points_dict or bp['quality'] > break_points_dict[t]['quality']:
                break_points_dict[t] = bp
        
        break_times = sorted(break_points_dict.keys())
        
        if not break_times:
            return segments
        
        adjusted_segments = []
        for segment in segments:
            original_start = segment['start']
            original_end = segment['end']
            original_duration = segment['duration']
            
            # Find best start point (prioritize quality, then proximity)
            snap_margin = 2.5  # Maximum seconds to adjust
            best_start = original_start
            best_start_score = 0
            
            for bt in break_times:
                diff = abs(bt - original_start)
                if diff <= snap_margin:
                    bp_data = break_points_dict.get(round(bt, 2), {})
                    quality = bp_data.get('quality', 0.5)
                    # Score = quality * proximity factor
                    proximity_score = 1 - (diff / snap_margin)
                    total_score = quality * 0.6 + proximity_score * 0.4
                    
                    # Prefer moving backward (earlier) for start
                    if bt <= original_start + 0.3:
                        total_score += 0.1
                    
                    if total_score > best_start_score:
                        best_start_score = total_score
                        best_start = bt
            
            # Find best end point (prioritize sentence-ending punctuation)
            best_end = original_end
            best_end_score = 0
            
            for bt in break_times:
                diff = abs(bt - original_end)
                if diff <= snap_margin:
                    bp_data = break_points_dict.get(round(bt, 2), {})
                    quality = bp_data.get('quality', 0.5)
                    bp_type = bp_data.get('type', 'end')
                    
                    # Prefer actual end points over start points
                    type_bonus = 0.2 if bp_type == 'end' else 0
                    
                    proximity_score = 1 - (diff / snap_margin)
                    total_score = quality * 0.5 + proximity_score * 0.3 + type_bonus
                    
                    # Prefer moving forward (later) for end to complete thoughts
                    if bt >= original_end - 0.3:
                        total_score += 0.1
                    
                    if total_score > best_end_score:
                        best_end_score = total_score
                        best_end = bt
            
            # Validate new duration
            new_duration = best_end - best_start
            min_duration = max(15, original_duration * 0.7)
            max_duration = original_duration * 1.35  # Slightly more flexibility
            
            if new_duration < min_duration or new_duration > max_duration:
                # Keep original if adjustment would break duration constraints
                adjusted_segments.append(segment)
            else:
                # Apply adjusted boundaries with quality metadata
                adjusted_segment = segment.copy()
                adjusted_segment['start'] = best_start
                adjusted_segment['end'] = best_end
                adjusted_segment['duration'] = new_duration
                adjusted_segment['context_adjusted'] = True
                adjusted_segment['boundary_quality'] = {
                    'start_score': best_start_score,
                    'end_score': best_end_score
                }
                adjusted_segments.append(adjusted_segment)
        
        adjusted_count = sum(1 for s in adjusted_segments if s.get('context_adjusted'))
        if adjusted_count > 0:
            print(f"🧠 Smart context-adjusted {adjusted_count}/{len(segments)} segment boundaries for coherent flow")
        
        return adjusted_segments

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
            
            # Only use segments between 10-50 seconds (expanded for extended duration)
            if 10 <= duration <= 50:
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
        Uses multiple segment lengths (short, medium, long) to maximize clip variety.
        OPTIMIZED for very long videos (>1 hour): creates appropriate segment lengths.
        """
        fallback_segments = []
        
        # Adaptive segment configs based on video duration
        long_video_threshold = getattr(self.config, 'LONG_VIDEO_THRESHOLD', 3600)  # 1 hour
        very_long_threshold = getattr(self.config, 'VERY_LONG_VIDEO_THRESHOLD', 7200)  # 2 hours
        
        if video_duration >= very_long_threshold:
            # Very long podcast (2+ hours): focus on longer, context-rich segments
            print(f"📺 Very long video detected ({video_duration/3600:.1f} hours) - using extended segment config")
            segment_configs = [
                (20, 0.5),   # Medium clips: 20s, 50% step
                (30, 0.6),   # Long clips: 30s, 60% step  
                (45, 0.65),  # Extended clips: 45s, 65% step - good for context
                (55, 0.7),   # Very extended: 55s, 70% step - max length for complete ideas
            ]
        elif video_duration >= long_video_threshold:
            # Long podcast (1-2 hours): balanced segment config
            print(f"📺 Long video detected ({video_duration/60:.1f} min) - using long video segment config")
            segment_configs = [
                (15, 0.5),   # Short clips: 15s, 50% step
                (25, 0.6),   # Medium clips: 25s, 60% step  
                (35, 0.7),   # Long clips: 35s, 70% step
                (50, 0.75),  # Extended clips: 50s, 75% step - for context
            ]
        else:
            # Normal video (<1 hour): standard config
            segment_configs = [
                (12, 0.5),   # Short clips: 12s, 50% step
                (20, 0.6),   # Medium clips: 20s, 60% step  
                (28, 0.7),   # Long clips: 28s, 70% step
                (45, 0.75),  # Extended clips: 45s, 75% step - for better context
            ]
        
        for segment_length, step_ratio in segment_configs:
            start_time = 0
            step = segment_length * step_ratio
            
            while start_time + segment_length <= video_duration + 5:  # Allow slight overflow
                end_time = min(start_time + segment_length, video_duration)
                actual_duration = end_time - start_time
                
                # Skip if segment is too short
                if actual_duration < 8:
                    start_time += step
                    continue
                
                # Find audio segments that overlap
                overlapping_audio = [
                    seg for seg in audio_segments
                    if self._segments_overlap((start_time, end_time), (seg['start'], seg['end']))
                ]
                
                # ALWAYS create segment if we have audio OR if duration is valid
                combined_text = ''
                avg_audio_scores = {}
                
                if overlapping_audio:
                    combined_text = ' '.join([seg.get('text', '') for seg in overlapping_audio])
                    avg_audio_scores = self._average_audio_scores(overlapping_audio)
                else:
                    # Even without matching audio, create segment for monolog
                    avg_audio_scores = {
                        'hook': 0.3, 'engagement': 0.4, 'educational': 0.3,
                        'emotional': 0.2, 'entertaining': 0.2
                    }
                
                fallback_segments.append({
                    'start': start_time,
                    'end': end_time,
                    'duration': actual_duration,
                    'text': combined_text or f'Segment {start_time:.0f}s - {end_time:.0f}s',
                    'visual': {
                        'has_faces': True,
                        'face_count': 1,
                        'has_closeup': True,
                        'motion_score': 0.35,
                        'has_high_motion': False,
                        'visual_engagement': 0.55  # Boosted for monolog
                    },
                    'audio': avg_audio_scores,
                    'is_fallback': True
                })
                
                start_time += step
        
        return fallback_segments
    
    def _create_emergency_segments(self, audio_segments: List[Dict], video_duration: float) -> List[Dict]:
        """
        EMERGENCY: Create segments directly from audio transcript when all else fails.
        Groups consecutive audio segments into clip-length chunks.
        """
        if not audio_segments:
            return []
        
        emergency_segments = []
        
        # Sort audio by start time
        sorted_audio = sorted(audio_segments, key=lambda x: x.get('start', 0))
        
        # Group into ~15-25 second chunks
        current_group = []
        group_start = 0
        
        for seg in sorted_audio:
            if not current_group:
                current_group = [seg]
                group_start = seg.get('start', 0)
            else:
                group_end = seg.get('end', seg.get('start', 0) + 5)
                group_duration = group_end - group_start
                
                if group_duration <= 25:
                    current_group.append(seg)
                else:
                    # Finalize current group
                    if current_group:
                        emergency_segments.append(
                            self._create_segment_from_audio_group(current_group, group_start)
                        )
                    # Start new group
                    current_group = [seg]
                    group_start = seg.get('start', 0)
        
        # Don't forget the last group
        if current_group:
            emergency_segments.append(
                self._create_segment_from_audio_group(current_group, group_start)
            )
        
        print(f"🆘 Emergency segments created: {len(emergency_segments)}")
        return emergency_segments
    
    def _create_segment_from_audio_group(self, audio_group: List[Dict], group_start: float) -> Dict:
        """Create a single segment from a group of audio segments."""
        group_end = max(seg.get('end', seg.get('start', 0) + 5) for seg in audio_group)
        combined_text = ' '.join([seg.get('text', '') for seg in audio_group])
        avg_scores = self._average_audio_scores(audio_group)
        
        return {
            'start': group_start,
            'end': group_end,
            'duration': group_end - group_start,
            'text': combined_text,
            'visual': {
                'has_faces': True,
                'face_count': 1,
                'has_closeup': True,
                'motion_score': 0.35,
                'has_high_motion': False,
                'visual_engagement': 0.5
            },
            'audio': avg_scores,
            'is_fallback': True,
            'is_emergency': True
        }
    
    def _average_audio_scores(self, segments: List[Dict]) -> Dict:
        """Average audio scores from multiple segments"""
        if not segments:
            # Return default scores instead of empty dict
            return {
                'hook': 0.3, 'emotional': 0.2, 'controversial': 0.1,
                'educational': 0.3, 'entertaining': 0.2, 'engagement': 0.4,
                'money': 0.1, 'urgency': 0.1, 'mental_slap': 0.1,
                'rare_topic': 0, 'meta_topic_strength': 0.1
            }
        
        keys = [
            'hook', 'emotional', 'controversial', 'educational', 'entertaining',
            'engagement', 'money', 'urgency', 'mental_slap',
            'rare_topic', 'meta_topic_strength'
        ]
        averaged = {}
        
        for key in keys:
            values = []
            for seg in segments:
                scores = seg.get('scores', {})
                if key in scores:
                    values.append(scores[key])
            averaged[key] = sum(values) / len(values) if values else 0.2  # Default 0.2 instead of 0
        
        meta_topics = []
        for seg in segments:
            scores = seg.get('scores', {})
            if scores.get('meta_topic'):
                meta_topics.append(scores['meta_topic'])
        if meta_topics:
            averaged['meta_topic'] = Counter(meta_topics).most_common(1)[0][0]
        
        return averaged
    
    def _analyze_narrative_context(self, segment: Dict, all_segments: List[Dict]) -> Dict:
        """
        Analyze narrative structure optimized for:
        1. TIMOTHY RONALD - Provocative, mental slap, direct hooks
        2. KALIMASADA (Prof Kaka) - Analytical, educational, rational crypto trading
        
        Timothy Ronald patterns:
        - Strong 3-second opening hooks
        - Direct/provocative statements  
        - Mental slap content
        - Money/investment topics
        - Emotional peaks
        
        Kalimasada patterns:
        - Analytical/scientific explanations
        - Crypto trading strategies
        - Educational/tutorial style
        - Psychology of trading
        - Rational decision making
        """
        text = (segment.get('text') or '').lower().strip()
        context_scores = {
            'has_opening_hook': 0.0,
            'has_conclusion': 0.0,
            'has_complete_thought': 0.0,
            'emotional_arc_position': 'neutral',
            'narrative_strength': 0.0,
            'is_timoty_signature': False,
            'is_kalimasada_signature': False,
            'content_type': 'general',
            'creator_style': 'general'
        }
        
        if not text:
            return context_scores
        
        # ============================================
        # TIMOTHY RONALD SIGNATURE OPENING HOOKS
        # These are his most viral opening patterns
        # ============================================
        timoty_hooks = [
            # Direct address style
            'bro', 'guys', 'lu', 'lo', 'kalian', 'anak muda',
            'dengerin', 'denger', 'listen', 'perhatiin', 'liat',
            'gue kasih tau', 'gw kasih tau', 'gue mau jelasin',
            # Provocative openings
            'tau gak', 'tau nggak', 'lo tau', 'lu tau',
            'kenapa', 'pernah gak', 'pernah nggak',
            'jujur', 'brutal', 'sadis', 'keras banget',
            # Attention grabbers
            'ini penting', 'stop', 'tunggu', 'sebelum lanjut',
            'yang ini', 'satu hal', 'fakta', 'rahasia',
            # Knowledge drops
            'gue bongkar', 'gw bongkar', 'ini cara', 'begini caranya',
            'kebanyakan orang', 'masalahnya', 'problemnya',
            # Money openers (Timothy specialty)
            'kalau mau kaya', 'mau cuan', 'mau duit', 'soal uang',
            'investasi', 'bisnis'
        ]
        
        # ============================================
        # KALIMASADA (PROF KAKA) SIGNATURE HOOKS
        # Analytical, educational, crypto-focused
        # ============================================
        kalimasada_hooks = [
            # Educational/tutorial openings
            'jadi gini', 'nah ini', 'perhatikan', 'coba lihat',
            'kita bahas', 'mari kita', 'sekarang kita',
            'saya jelaskan', 'saya kasih tau', 'saya tunjukkan',
            # Analytical openings
            'secara teknikal', 'secara fundamental', 'dari data',
            'kalau kita lihat', 'berdasarkan', 'menurut analisis',
            'faktanya', 'data menunjukkan', 'historis',
            # Crypto-specific hooks
            'bitcoin', 'ethereum', 'btc', 'eth', 'crypto', 'kripto',
            'market', 'chart', 'trend', 'bullish', 'bearish',
            'altcoin', 'token', 'blockchain',
            # Strategy openings
            'strategi', 'strategy', 'cara trading', 'teknik',
            'money management', 'risk management', 'position sizing',
            # Academic/professor style
            'yang perlu dipahami', 'konsepnya', 'prinsipnya',
            'logikanya', 'secara rasional', 'ilmiahnya'
        ]
        
        # Standard opening patterns
        general_hooks = [
            'jadi', 'nah', 'oke', 'so', 'ok so', 'alright',
            'pertama', 'sebelum', 'first', 'before'
        ]
        
        # Check for signatures (highest priority)
        hook_detected = False
        
        # Check Timothy hooks
        for pattern in timoty_hooks:
            if text.startswith(pattern) or text[:40].find(pattern) != -1:
                context_scores['has_opening_hook'] = 1.0
                context_scores['is_timoty_signature'] = True
                context_scores['creator_style'] = 'timoty'
                hook_detected = True
                break
        
        # Check Kalimasada hooks (can coexist for crypto content)
        for pattern in kalimasada_hooks:
            if text.startswith(pattern) or text[:50].find(pattern) != -1:
                context_scores['has_opening_hook'] = max(context_scores['has_opening_hook'], 0.95)
                context_scores['is_kalimasada_signature'] = True
                if context_scores['creator_style'] == 'general':
                    context_scores['creator_style'] = 'kalimasada'
                elif context_scores['creator_style'] == 'timoty':
                    context_scores['creator_style'] = 'both'  # Collaboration content
                hook_detected = True
                break
        
        # Fallback to general hooks
        if not hook_detected:
            for pattern in general_hooks:
                if text.startswith(pattern) or text[:25].find(pattern) != -1:
                    context_scores['has_opening_hook'] = 0.7
                    break
        
        # ============================================
        # CONCLUSION PATTERNS (Both creators)
        # ============================================
        timoty_conclusions = [
            'catat', 'catet', 'ingat', 'inget', 'remember',
            'praktekin', 'lakuin', 'apply', 'do it',
            'mulai sekarang', 'dari sekarang', 'hari ini',
            'jadi intinya', 'intinya', 'kesimpulan', 'poinnya',
            'makanya', 'karena itu', 'itu sebabnya',
            'yang penting', 'kuncinya', 'rahasianya',
            'titik', 'selesai', 'udah', 'enough', 'cukup'
        ]
        
        kalimasada_conclusions = [
            # Academic conclusions
            'kesimpulannya', 'jadi kesimpulan', 'summary',
            'ringkasnya', 'singkatnya', 'intinya begini',
            # Action-oriented (trading)
            'jadi yang harus dilakukan', 'action plan',
            'langkah selanjutnya', 'next step',
            # Strategy conclusions
            'dengan strategi ini', 'gunakan strategi',
            'terapkan', 'implementasi',
            # Risk warnings
            'tapi ingat', 'disclaimer', 'resiko',
            'jangan lupa', 'perhatikan resiko'
        ]
        
        for pattern in timoty_conclusions + kalimasada_conclusions:
            if pattern in text:
                context_scores['has_conclusion'] = 0.85
                break
        
        # ============================================
        # MENTAL SLAP DETECTION (Timothy specialty)
        # ============================================
        mental_slap_patterns = [
            'bangun', 'wake up', 'sadar', 'sadarlah', 'buka mata',
            'jangan nangis', 'jangan manja', 'stop excuse',
            'emang hidup gampang', 'emang enak', 'mau gampang',
            'salah lu', 'salah lo', 'itu salah',
            'bego', 'tolol', 'bodoh', 'stupid',
            'kenyataan', 'realita', 'truth', 'faktanya',
            'pahit', 'keras', 'kejam', 'brutal',
            'kalau gak mau', 'kalo ga mau', 'ya udah',
            'terserah', 'up to you', 'pilihan lu'
        ]
        
        mental_slap_count = sum(1 for p in mental_slap_patterns if p in text)
        if mental_slap_count >= 2:
            context_scores['content_type'] = 'mental_slap'
            context_scores['narrative_strength'] += 0.3
            context_scores['is_timoty_signature'] = True
        
        # ============================================
        # CRYPTO TRADING DETECTION (Kalimasada specialty)
        # ============================================
        crypto_trading_patterns = [
            # Trading terminology
            'trading', 'trader', 'trade', 'buy', 'sell', 'hold',
            'entry', 'exit', 'stop loss', 'take profit', 'tp', 'sl',
            'leverage', 'margin', 'spot', 'futures', 'perpetual',
            # Analysis terms
            'support', 'resistance', 'breakout', 'breakdown',
            'trend', 'reversal', 'consolidation', 'sideways',
            'bullish', 'bearish', 'pump', 'dump', 'correction',
            # Indicators
            'rsi', 'macd', 'moving average', 'ma', 'ema', 'sma',
            'fibonacci', 'fib', 'volume', 'candle', 'candlestick',
            # Risk/money management
            'risk reward', 'rr', 'position size', 'lot',
            'money management', 'mm', 'portfolio', 'alokasi',
            # Crypto specifics
            'halving', 'defi', 'dex', 'exchange', 'wallet',
            'staking', 'yield', 'apy', 'apr', 'gas fee'
        ]
        
        crypto_count = sum(1 for p in crypto_trading_patterns if p in text)
        if crypto_count >= 3:
            context_scores['content_type'] = 'crypto_trading'
            context_scores['narrative_strength'] += 0.28
            context_scores['is_kalimasada_signature'] = True
        elif crypto_count >= 2:
            if context_scores['content_type'] == 'general':
                context_scores['content_type'] = 'crypto_trading'
            context_scores['narrative_strength'] += 0.15
        
        # ============================================
        # MONEY/INVESTMENT DETECTION (Both creators)
        # ============================================
        money_patterns = [
            'uang', 'duit', 'cuan', 'profit', 'untung', 'rugi',
            'investasi', 'invest', 'saham', 'crypto', 'bitcoin',
            'kaya', 'rich', 'wealthy', 'millionaire', 'milyarder',
            'passive income', 'cashflow', 'omset', 'revenue',
            'gaji', 'salary', 'income', 'penghasilan',
            'asset', 'aset', 'portofolio', 'portfolio',
            'closing', 'deal', 'sales', 'jualan'
        ]
        
        money_count = sum(1 for p in money_patterns if p in text)
        if money_count >= 2 and context_scores['content_type'] == 'general':
            context_scores['content_type'] = 'money_talk'
            context_scores['narrative_strength'] += 0.25
        
        # ============================================  
        # EDUCATIONAL/TUTORIAL DETECTION (Kalimasada emphasis)
        # ============================================
        educational_patterns = [
            # Teaching language
            'caranya', 'langkahnya', 'step by step', 'tutorial',
            'belajar', 'pelajari', 'pahami', 'mengerti',
            'contoh', 'misalnya', 'ilustrasi', 'case study',
            # Explanation markers
            'artinya', 'maksudnya', 'definisi', 'pengertian',
            'kenapa bisa', 'alasannya', 'penyebab',
            'cara kerja', 'mekanisme', 'prosesnya',
            # Academic tone
            'secara teori', 'prakteknya', 'aplikasinya',
            'fundamental', 'prinsip dasar', 'konsep'
        ]
        
        edu_count = sum(1 for p in educational_patterns if p in text)
        if edu_count >= 2:
            if context_scores['content_type'] == 'general':
                context_scores['content_type'] = 'educational'
            context_scores['narrative_strength'] += 0.2
            if crypto_count >= 1:  # Educational + crypto = Kalimasada
                context_scores['is_kalimasada_signature'] = True
        
        # ============================================
        # MINDSET/MOTIVATION DETECTION
        # ============================================
        mindset_patterns = [
            'mindset', 'mental', 'pikiran', 'cara pikir',
            'sukses', 'success', 'berhasil', 'achieve',
            'gagal', 'failure', 'jatuh', 'bangkit',
            'disiplin', 'discipline', 'konsisten', 'consistent',
            'fokus', 'focus', 'target', 'goal',
            'kerja keras', 'hustle', 'grind', 'effort',
            'psikologi', 'psychology', 'emosi', 'emotion',
            'sabar', 'patience', 'fomo', 'fear', 'greed'
        ]
        
        mindset_count = sum(1 for p in mindset_patterns if p in text)
        if mindset_count >= 2:
            if context_scores['content_type'] == 'general':
                context_scores['content_type'] = 'mindset'
            context_scores['narrative_strength'] += 0.2
        
        # ============================================
        # COMPLETE THOUGHT ANALYSIS
        # ============================================
        sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        complete_sentences = sum(1 for s in sentences if len(s.split()) >= 5)
        
        if complete_sentences >= 3:
            context_scores['has_complete_thought'] = 0.8
        elif complete_sentences >= 2:
            context_scores['has_complete_thought'] = 0.6
        elif complete_sentences >= 1:
            context_scores['has_complete_thought'] = 0.4
        
        # ============================================
        # EMOTIONAL ARC DETECTION
        # ============================================
        exclamation_count = text.count('!')
        question_count = text.count('?')
        
        # Intensity words
        intensity_words = [
            'banget', 'sekali', 'parah', 'gila', 'crazy',
            'luar biasa', 'amazing', 'incredible', 'fantastis',
            'penting banget', 'harus', 'wajib', 'must',
            'serius', 'seriously', 'literally', 'beneran'
        ]
        intensity_count = sum(1 for w in intensity_words if w in text)
        
        # Determine emotional arc
        if (intensity_count >= 3 or exclamation_count >= 3 or 
            (mental_slap_count >= 2 and intensity_count >= 1)):
            context_scores['emotional_arc_position'] = 'climax'
            context_scores['narrative_strength'] = max(context_scores['narrative_strength'], 0.95)
        elif context_scores['has_opening_hook'] > 0.7:
            context_scores['emotional_arc_position'] = 'buildup'
            context_scores['narrative_strength'] = max(context_scores['narrative_strength'], 0.75)
        elif context_scores['has_conclusion'] > 0.7:
            context_scores['emotional_arc_position'] = 'resolution'
            context_scores['narrative_strength'] = max(context_scores['narrative_strength'], 0.8)
        else:
            context_scores['narrative_strength'] = max(context_scores['narrative_strength'], 0.4)
        
        # Bonus for questions (engagement)
        if question_count > 0:
            context_scores['narrative_strength'] += 0.1
        
        # Signature content boosts
        if context_scores['is_timoty_signature']:
            context_scores['narrative_strength'] = min(1.0, context_scores['narrative_strength'] + 0.15)
        if context_scores['is_kalimasada_signature']:
            context_scores['narrative_strength'] = min(1.0, context_scores['narrative_strength'] + 0.15)
        
        # ============================================
        # HIGH IQ ANALYSIS: Rhetorical Devices
        # These make content more memorable and shareable
        # ============================================
        
        # 1. METAPHOR/ANALOGY Detection (makes complex ideas simple)
        analogy_patterns = [
            'seperti', 'kayak', 'ibarat', 'seolah', 'mirip',
            'analoginya', 'contohnya kayak', 'bayangin', 'coba bayangin',
            'like', 'as if', 'imagine', 'think of it as', 'it\'s like'
        ]
        has_analogy = any(p in text for p in analogy_patterns)
        if has_analogy:
            context_scores['narrative_strength'] += 0.08
            context_scores['has_rhetorical_device'] = True
        
        # 2. CONTRAST/COMPARISON (before/after, us/them)
        contrast_patterns = [
            'sebelum vs', 'dulu vs', 'before vs', 'vs', 
            'bedanya', 'perbedaannya', 'beda sama', 'kebalikannya',
            'sementara', 'sedangkan', 'padahal', 'tapi kenyataannya',
            'orang sukses', 'orang gagal', 'yang kaya', 'yang miskin',
            'winner', 'loser', 'mindset kaya', 'mindset miskin',
            'sebelum', 'sesudah', 'before', 'after', 'dulu', 'sekarang'
        ]
        contrast_count = sum(1 for p in contrast_patterns if p in text)
        if contrast_count >= 2:
            context_scores['narrative_strength'] += 0.12
            context_scores['has_contrast'] = True
        elif contrast_count >= 1:
            context_scores['narrative_strength'] += 0.06
        
        # 3. REPETITION (for emphasis - viral technique)
        words = text.split()
        word_freq = {}
        for w in words:
            w = w.lower().strip('.,!?')
            if len(w) > 3:  # Only meaningful words
                word_freq[w] = word_freq.get(w, 0) + 1
        
        repeated_words = [w for w, count in word_freq.items() if count >= 3]
        if repeated_words:
            context_scores['narrative_strength'] += 0.05
            context_scores['has_repetition'] = True
        
        # 4. POWER NUMBERS (specific numbers are more credible)
        number_patterns = [
            r'\d+%', r'\d+ persen', r'\d+x', r'\d+ kali',
            r'\d+ juta', r'\d+ milyar', r'\d+ tahun', r'\d+ bulan',
            r'\d+ hari', r'\d+ jam', r'\d+ langkah', r'\d+ cara',
            r'pertama', r'kedua', r'ketiga', r'step \d', r'langkah \d'
        ]
        import re as regex_module
        number_count = sum(1 for pattern in number_patterns 
                         if regex_module.search(pattern, text))
        if number_count >= 2:
            context_scores['narrative_strength'] += 0.1
            context_scores['has_power_numbers'] = True
        elif number_count >= 1:
            context_scores['narrative_strength'] += 0.05
        
        # ============================================
        # HIGH EQ ANALYSIS: Emotional Intelligence
        # Understanding and triggering audience emotions
        # ============================================
        
        # 1. PAIN POINT TARGETING (EQ - understanding audience struggles)
        pain_patterns = [
            # Financial pain
            'gak punya uang', 'bokek', 'kantong kering', 'dompet tipis',
            'gaji abis', 'gak cukup', 'pas-pasan', 'debt', 'utang',
            # Career pain
            'stuck', 'mentok', 'gak naik', 'jalan di tempat', 'bingung',
            'gak tau mau', 'lost', 'gak ada arah', 'no direction',
            # Relationship pain  
            'ditolak', 'di-ghosting', 'gak dihargai', 'diabaikan',
            # Self-esteem pain
            'gak pede', 'minder', 'insecure', 'takut', 'ragu',
            'overthinking', 'gak berani', 'malu'
        ]
        pain_count = sum(1 for p in pain_patterns if p in text)
        if pain_count >= 2:
            context_scores['narrative_strength'] += 0.15
            context_scores['targets_pain_point'] = True
            context_scores['eq_score'] = context_scores.get('eq_score', 0) + 0.3
        elif pain_count >= 1:
            context_scores['narrative_strength'] += 0.08
            context_scores['eq_score'] = context_scores.get('eq_score', 0) + 0.15
        
        # 2. ASPIRATION TRIGGERING (what audience wants to become)
        aspiration_patterns = [
            'jadi kaya', 'bebas finansial', 'financial freedom', 'passive income',
            'sukses', 'berhasil', 'achieve', 'accomplish', 'goal',
            'impian', 'dream', 'mimpi jadi kenyataan', 'make it happen',
            'level up', 'naik level', 'upgrade', 'transformasi',
            'jadi boss', 'jadi bos', 'own business', 'punya bisnis',
            'percaya diri', 'confident', 'respected', 'dihormati'
        ]
        aspiration_count = sum(1 for p in aspiration_patterns if p in text)
        if aspiration_count >= 2:
            context_scores['narrative_strength'] += 0.12
            context_scores['triggers_aspiration'] = True
            context_scores['eq_score'] = context_scores.get('eq_score', 0) + 0.25
        elif aspiration_count >= 1:
            context_scores['narrative_strength'] += 0.06
            context_scores['eq_score'] = context_scores.get('eq_score', 0) + 0.12
        
        # 3. SOCIAL PROOF (builds trust through others' experiences)
        social_proof_patterns = [
            'banyak orang', 'kebanyakan', 'orang-orang sukses', 'mereka yang',
            'client gue', 'murid gue', 'banyak yang', 'rata-rata',
            'research', 'studi', 'menurut', 'data menunjukkan',
            'terbukti', 'proven', 'sudah banyak', 'millions of'
        ]
        social_proof_count = sum(1 for p in social_proof_patterns if p in text)
        if social_proof_count >= 2:
            context_scores['narrative_strength'] += 0.1
            context_scores['has_social_proof'] = True
        
        # 4. URGENCY/SCARCITY (FOMO triggering)
        urgency_patterns = [
            'sekarang', 'now', 'segera', 'immediately', 'hari ini',
            'jangan tunggu', 'don\'t wait', 'kesempatan', 'opportunity',
            'terbatas', 'limited', 'akan hilang', 'nanti terlambat',
            'mumpung', 'selagi', 'while you can', 'before it\'s too late',
            'kalau gak sekarang, kapan', 'nunda terus', 'procrastinate'
        ]
        urgency_count = sum(1 for p in urgency_patterns if p in text)
        if urgency_count >= 2:
            context_scores['narrative_strength'] += 0.12
            context_scores['creates_urgency'] = True
            context_scores['eq_score'] = context_scores.get('eq_score', 0) + 0.2
        
        # ============================================
        # STORYTELLING ARC ANALYSIS 
        # Great content follows story structures
        # ============================================
        
        # Check for storytelling elements
        story_elements = {
            'has_setup': any(p in text for p in ['waktu itu', 'dulu gue', 'awalnya', 'at first', 'initially']),
            'has_conflict': any(p in text for p in ['masalahnya', 'tapi', 'sayangnya', 'unfortunately', 'the problem']),
            'has_resolution': any(p in text for p in ['akhirnya', 'finally', 'ternyata', 'solusinya', 'the answer'])
        }
        
        story_element_count = sum(1 for v in story_elements.values() if v)
        if story_element_count >= 2:
            context_scores['narrative_strength'] += 0.15
            context_scores['has_story_arc'] = True
        elif story_element_count >= 1:
            context_scores['narrative_strength'] += 0.07
        
        # ============================================
        # CALL TO ACTION STRENGTH
        # Strong CTAs drive engagement
        # ============================================
        cta_patterns = [
            # Direct commands
            'lakuin', 'coba', 'mulai', 'start', 'go', 'do it',
            'praktekin', 'apply', 'implementasi', 'execute',
            # Soft CTAs
            'share ini', 'bagikan', 'save for later', 'bookmark',
            'comment', 'komen', 'dm gue', 'hubungi',
            # Engagement CTAs
            'setuju gak', 'gimana menurut', 'what do you think',
            'pernah gak', 'ada yang', 'siapa yang'
        ]
        cta_count = sum(1 for p in cta_patterns if p in text)
        if cta_count >= 2:
            context_scores['narrative_strength'] += 0.1
            context_scores['has_strong_cta'] = True
        elif cta_count >= 1:
            context_scores['narrative_strength'] += 0.05
        
        # Final normalization
        context_scores['narrative_strength'] = min(1.0, context_scores['narrative_strength'])
        context_scores['eq_score'] = min(1.0, context_scores.get('eq_score', 0))
        
        # Calculate overall IQ/EQ quality score
        iq_signals = sum([
            context_scores.get('has_rhetorical_device', False),
            context_scores.get('has_contrast', False),
            context_scores.get('has_power_numbers', False),
            context_scores.get('has_story_arc', False)
        ])
        
        eq_signals = sum([
            context_scores.get('targets_pain_point', False),
            context_scores.get('triggers_aspiration', False),
            context_scores.get('creates_urgency', False),
            context_scores.get('has_social_proof', False)
        ])
        
        context_scores['iq_quality'] = min(1.0, iq_signals * 0.25)
        context_scores['eq_quality'] = min(1.0, eq_signals * 0.25)
        context_scores['overall_iq_eq_score'] = (context_scores['iq_quality'] + context_scores['eq_quality']) / 2
        
        return context_scores
    
    def _detect_idea_boundaries(self, segment: Dict, audio_segments: List[Dict]) -> Dict:
        """
        Like a person with high EQ, detect where ideas start and end.
        Ensures we don't cut in the middle of a thought.
        """
        text = (segment.get('text') or '').strip()
        start = segment.get('start', 0)
        end = segment.get('end', 0)
        
        boundary_quality = {
            'start_quality': 0.5,  # 0 = mid-sentence, 1 = clean start
            'end_quality': 0.5,    # 0 = mid-sentence, 1 = clean end
            'idea_completeness': 0.5
        }
        
        if not text or not audio_segments:
            return boundary_quality
        
        # Find the actual transcript segments that overlap with this clip
        overlapping = [
            seg for seg in audio_segments
            if seg.get('end', 0) > start and seg.get('start', 0) < end
        ]
        
        if not overlapping:
            return boundary_quality
        
        # Check if we start at the beginning of a transcript segment
        first_overlap = min(overlapping, key=lambda x: x.get('start', 0))
        if abs(first_overlap.get('start', 0) - start) < 0.5:
            boundary_quality['start_quality'] = 1.0  # Clean start
        elif abs(first_overlap.get('start', 0) - start) < 1.5:
            boundary_quality['start_quality'] = 0.7
        
        # Check if we end at the end of a transcript segment
        last_overlap = max(overlapping, key=lambda x: x.get('end', 0))
        if abs(last_overlap.get('end', 0) - end) < 0.5:
            boundary_quality['end_quality'] = 1.0  # Clean end
        elif abs(last_overlap.get('end', 0) - end) < 1.5:
            boundary_quality['end_quality'] = 0.7
        
        # Check for sentence-ending punctuation
        if text.rstrip().endswith(('.', '!', '?')):
            boundary_quality['end_quality'] += 0.2
        
        # Idea completeness: penalize very short text or incomplete sentences
        word_count = len(text.split())
        if word_count >= 30:
            boundary_quality['idea_completeness'] = 1.0
        elif word_count >= 15:
            boundary_quality['idea_completeness'] = 0.7
        else:
            boundary_quality['idea_completeness'] = 0.4
        
        return boundary_quality
    
    def _validate_semantic_context(self, segment: Dict, audio_segments: List[Dict]) -> Dict:
        """
        Validate that a clip has complete semantic context.
        Checks for:
        - Incomplete sentence patterns
        - Dangling references (pronouns without antecedent)
        - Unresolved questions
        - Context completeness score
        
        Returns context validation scores.
        """
        text = (segment.get('text') or '').strip()
        text_lower = text.lower()
        
        validation = {
            'context_complete': True,
            'confidence': 0.5,
            'issues': [],
            'suggestions': []
        }
        
        if not text:
            validation['context_complete'] = False
            validation['confidence'] = 0.0
            return validation
        
        # === CHECK 1: Incomplete Sentence Patterns ===
        # Sentences that start with conjunctions suggesting prior context
        incomplete_start_patterns = [
            'tapi kan', 'dan juga', 'terus yang', 'makanya tadi', 'kayak tadi',
            'seperti yang', 'yang tadi', 'itu tadi', 'jadi tadi', 'nah tadi',
            'but also', 'and also', 'as I said', 'like I mentioned', 'that\'s why I'
        ]
        
        starts_incomplete = any(text_lower.startswith(p) for p in incomplete_start_patterns)
        if starts_incomplete:
            validation['issues'].append('starts_with_prior_reference')
            validation['confidence'] -= 0.2
        
        # === CHECK 2: Dangling Pronouns at Start ===
        # Clips starting with pronouns referring to something not in clip
        dangling_pronouns = [
            'itu ', 'ini ', 'dia ', 'mereka ', 'kita tadi', 'lu tadi', 'gue tadi',
            'it ', 'they ', 'this ', 'that ', 'he said', 'she said', 'those '
        ]
        
        has_dangling_start = any(text_lower.startswith(p) for p in dangling_pronouns)
        if has_dangling_start:
            validation['issues'].append('dangling_pronoun_start')
            validation['confidence'] -= 0.15
        
        # === CHECK 3: Unfinished Thoughts at End ===
        # Clips ending mid-sentence
        unfinished_end_patterns = [
            ' jadi', ' terus', ' dan', ' tapi', ' atau', ' karena', ' supaya',
            ' agar', ' ketika', ' saat', ' kalau', ' if', ' when', ' because',
            ' so', ' and', ' but', ' or'
        ]
        
        ends_incomplete = any(text_lower.rstrip().endswith(p) for p in unfinished_end_patterns)
        if ends_incomplete:
            validation['issues'].append('ends_mid_sentence')
            validation['confidence'] -= 0.25
            validation['suggestions'].append('extend_end_point')
        
        # === CHECK 4: Question Without Answer ===
        # If clip contains a question, check if there's follow-up in same clip
        question_count = text.count('?')
        if question_count > 0:
            # Check if there's content after the question
            last_question_idx = text.rfind('?')
            content_after_question = text[last_question_idx + 1:].strip()
            
            if len(content_after_question) < 20:  # Very little after question
                validation['issues'].append('unanswered_question')
                validation['confidence'] -= 0.1
                validation['suggestions'].append('extend_to_include_answer')
        
        # === CHECK 5: Context Completeness via Word Count ===
        word_count = len(text.split())
        if word_count < 10:
            validation['issues'].append('too_short_for_context')
            validation['confidence'] -= 0.2
        elif word_count >= 25:
            validation['confidence'] += 0.1  # Bonus for sufficient length
        
        # === CHECK 6: Has Complete Idea Marker ===
        complete_idea_markers = [
            'jadi intinya', 'kesimpulannya', 'poinnya adalah', 'yang penting',
            'the point is', 'in summary', 'bottom line', 'the key is',
            'ingat ya', 'catat ini', 'ini penting', 'remember this'
        ]
        
        has_complete_marker = any(m in text_lower for m in complete_idea_markers)
        if has_complete_marker:
            validation['confidence'] += 0.2
            validation['context_complete'] = True
        
        # Normalize confidence
        validation['confidence'] = max(0.0, min(1.0, validation['confidence']))
        
        # Determine overall context completeness
        if validation['confidence'] < 0.3 or len(validation['issues']) >= 3:
            validation['context_complete'] = False
        
        return validation
    
    def _score_segments(self, segments: List[Dict], style: str) -> List[Dict]:
        """
        Score each segment for clip potential with HIGH IQ/EQ analysis.
        Optimized for Timothy Ronald & Kalimasada content patterns.
        """
        print(f"📊 Scoring segments with Timothy Ronald & Kalimasada optimization (style: {style})...")
        
        scored = []
        
        for segment in segments:
            # Calculate base viral score
            viral_score = self._calculate_viral_score(segment, style)
            
            # HIGH IQ ANALYSIS: Narrative context
            narrative_context = self._analyze_narrative_context(segment, segments)
            
            # Apply narrative bonuses (smart understanding of content flow)
            if narrative_context['has_opening_hook'] > 0.7:
                viral_score += 0.15  # Strong hooks are gold
            elif narrative_context['has_opening_hook'] > 0.5:
                viral_score += 0.10
                
            if narrative_context['has_conclusion'] > 0.7:
                viral_score += 0.12  # Strong conclusions
            elif narrative_context['has_conclusion'] > 0.5:
                viral_score += 0.08
                
            if narrative_context['has_complete_thought'] > 0.6:
                viral_score += 0.10  # Complete ideas are more shareable
            elif narrative_context['has_complete_thought'] > 0.4:
                viral_score += 0.05
            
            # CONTENT TYPE BONUSES (Both creators)
            content_type = narrative_context.get('content_type', 'general')
            
            # Timothy Ronald specialties
            if content_type == 'mental_slap':
                viral_score += 0.18  # Mental slap is Timothy's specialty
            elif content_type == 'money_talk':
                viral_score += 0.15  # Money content is their core
            elif content_type == 'mindset':
                viral_score += 0.12  # Mindset content performs well
            
            # Kalimasada specialties
            elif content_type == 'crypto_trading':
                viral_score += 0.20  # Crypto trading is Kalimasada's specialty
            elif content_type == 'educational':
                viral_score += 0.15  # Educational content (Prof Kaka style)
            
            # CONVERSATIONAL METRICS (New)
            # Boost score for dynamic conversations (2-person podcasts)
            if segment.get('is_conversation', False):
                # Balanced conversation bonus
                left = segment.get('speaker_left_ratio', 0)
                right = segment.get('speaker_right_ratio', 0)
                if left > 0.1 and right > 0.1:
                    viral_score += 0.12  # Bonus for active back-and-forth
            
            # CREATOR SIGNATURE BONUSES
            if narrative_context.get('is_timoty_signature'):
                viral_score += 0.15  # Timothy signature patterns
            if narrative_context.get('is_kalimasada_signature'):
                viral_score += 0.15  # Kalimasada signature patterns
            
            # Creator style identification (for metadata)
            creator_style = narrative_context.get('creator_style', 'general')
            
            # Emotional arc position bonus
            if narrative_context['emotional_arc_position'] == 'climax':
                viral_score += 0.18  # Emotional peaks are highly engaging
            elif narrative_context['emotional_arc_position'] == 'resolution':
                viral_score += 0.10  # Good endings satisfy viewers
            elif narrative_context['emotional_arc_position'] == 'buildup':
                viral_score += 0.05  # Setup content
            
            # Narrative strength contributes to overall score
            viral_score += narrative_context['narrative_strength'] * 0.12
            
            # IQ/EQ QUALITY BONUSES (Premium content detection)
            iq_quality = narrative_context.get('iq_quality', 0)
            eq_quality = narrative_context.get('eq_quality', 0)
            overall_iq_eq = narrative_context.get('overall_iq_eq_score', 0)
            
            # High IQ content (rhetorical devices, story arcs, power numbers)
            if iq_quality >= 0.75:
                viral_score += 0.15  # Premium IQ content
            elif iq_quality >= 0.5:
                viral_score += 0.08
            elif iq_quality >= 0.25:
                viral_score += 0.04
            
            # High EQ content (pain points, aspirations, urgency, social proof)
            if eq_quality >= 0.75:
                viral_score += 0.18  # Premium EQ content - highly engaging
            elif eq_quality >= 0.5:
                viral_score += 0.10
            elif eq_quality >= 0.25:
                viral_score += 0.05
            
            # Synergy bonus: content with BOTH high IQ and EQ is exceptional
            if iq_quality >= 0.5 and eq_quality >= 0.5:
                viral_score += 0.12  # IQ/EQ synergy bonus
            
            # Determine category
            category = self._determine_category(segment)
            
            # Check if duration is suitable
            suitable_duration = self._check_duration_suitability(segment['duration'])
            
            # SEMANTIC CONTEXT VALIDATION
            # Validate that clip has complete, coherent context
            semantic_validation = self._validate_semantic_context(segment, segments)
            
            # Apply penalty for incomplete context
            if not semantic_validation['context_complete']:
                viral_score *= 0.7  # Significant penalty for incomplete context
            elif semantic_validation['confidence'] < 0.4:
                viral_score *= 0.85  # Moderate penalty for low confidence
            elif semantic_validation['confidence'] > 0.7:
                viral_score += 0.05  # Small bonus for high confidence context
            
            scored.append({
                **segment,
                'viral_score': min(1.0, max(0.0, viral_score)),
                'category': category,
                'suitable_duration': suitable_duration,
                'narrative_context': narrative_context,
                'content_type': content_type,
                'creator_style': creator_style,
                'semantic_context': semantic_validation
            })
        
        # Sort by viral score
        scored.sort(key=lambda x: x['viral_score'], reverse=True)
        
        # Log context quality stats
        complete_context_count = sum(1 for s in scored if s.get('semantic_context', {}).get('context_complete', False))
        
        # IQ/EQ quality stats
        high_iq_count = sum(1 for s in scored if s.get('narrative_context', {}).get('iq_quality', 0) >= 0.5)
        high_eq_count = sum(1 for s in scored if s.get('narrative_context', {}).get('eq_quality', 0) >= 0.5)
        premium_count = sum(1 for s in scored 
                          if s.get('narrative_context', {}).get('iq_quality', 0) >= 0.5 
                          and s.get('narrative_context', {}).get('eq_quality', 0) >= 0.5)
        
        print(f"   🧠 Applied HIGH IQ/EQ context analysis to {len(scored)} segments")
        print(f"   📝 Context: {complete_context_count}/{len(scored)} complete | IQ≥50%: {high_iq_count} | EQ≥50%: {high_eq_count} | Premium: {premium_count}")
        
        # Show top 3 IQ/EQ scores if available
        if scored and len(scored) >= 3:
            top3_iq = [s.get('narrative_context', {}).get('iq_quality', 0) for s in scored[:3]]
            top3_eq = [s.get('narrative_context', {}).get('eq_quality', 0) for s in scored[:3]]
            print(f"   ⭐ Top 3 clips - IQ: {[f'{x:.0%}' for x in top3_iq]} | EQ: {[f'{x:.0%}' for x in top3_eq]}")
        
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
            visual_bonus += 0.05
        
        # ENTERPRISE: Visual-Audio Coherence (Ghost Speaker Check)
        # Penalize if audio is active but visual subject is NOT talking
        # This prevents "Reaction Shot" clips where we hear someone else talking
        is_talking_visual = visual.get('is_talking', True) # Default true if missing
        if not is_talking_visual and not is_fallback:
             # Only penalize if we are sure faces are present but not moving lips
             if visual.get('has_faces') and visual.get('face_count', 0) > 0:
                 total_score *= 0.65  # Heavy penalty for off-screen speaker focus
        
        # ENTERPRISE: Pacing Score (WPM)
        # Favor energetic delivery (130-180 WPM)
        duration_mins = max(segment['duration'], 1) / 60.0
        word_count = len(segment.get('text', '').split())
        wpm = word_count / duration_mins
        
        if 130 <= wpm <= 190:
            content_value += 0.08 # Sweet spot
        elif wpm < 100:
            content_value -= 0.05 # Too slow/boring
        elif wpm > 220:
            content_value -= 0.05 # Too fast/unclear

        
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

        if is_fallback:
            fallback_floor = getattr(self.config, 'FALLBACK_VIRAL_SCORE', 0.15) + 0.05
            total_score = max(total_score, fallback_floor)
        
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
        """Check which duration category this segment fits while respecting config min."""
        min_short = 15.0  # Enforce 15s minimum for quality context

        if duration < min_short:
            return 'custom'
        if duration <= 18:
            return 'short'
        if duration <= 28:
            return 'medium'
        if duration <= 42:
            return 'long'
        if duration <= 55:
            return 'extended'
        return 'extended'
    
    def _select_clips(self, scored_segments: List[Dict], target_duration: str) -> List[Dict]:
        """Select clip segments quickly while guaranteeing minimum output."""
        print(f"🎯 Selecting clips (target: {target_duration})...")
        
        if not scored_segments:
            print("⚠️ No scored segments to select from!")
            return []
        
        selected = []

        selected = []

        min_duration = 15.0  # Enforce 15s minimum for selection


        def duration_ok(segment: Dict) -> bool:
            return segment.get('duration', 0) >= min_duration

        fallback_segments = [
            s for s in scored_segments
            if s.get('is_fallback') and duration_ok(s)
        ]
        print(f"   Fallback segments available: {len(fallback_segments)}")

        if target_duration != 'all':
            candidates = [s for s in scored_segments if s.get('suitable_duration') == target_duration]
        else:
            candidates = [s for s in scored_segments if s.get('suitable_duration') != 'custom']
        
        candidates = [s for s in candidates if duration_ok(s)]
        print(f"   Duration-matched candidates: {len(candidates)}")

        if not candidates:
            candidates = self._adjust_segment_durations(scored_segments, target_duration)
            candidates = [s for s in candidates if duration_ok(s)]
            print(f"   After duration adjustment: {len(candidates)}")

        # Still empty? fall back to any segments (including fallback ones)
        if not candidates and scored_segments:
            candidates = scored_segments[:]
            candidates = [s for s in candidates if duration_ok(s)]
            print(f"   Using all scored segments: {len(candidates)}")

        # Give priority to fallback monolog segments when no standard candidates available
        if fallback_segments and len(candidates) < getattr(self.config, 'MIN_CLIP_OUTPUT', 5):
            # extend while preserving order and avoiding duplicates
            seen_ids = set(id(seg) for seg in candidates)
            for seg in fallback_segments:
                if not duration_ok(seg):
                    continue
                if id(seg) not in seen_ids:
                    candidates.append(seg)
                    seen_ids.add(id(seg))
            print(f"   After adding fallback priority: {len(candidates)}")

        max_clips = max(1, getattr(self.config, 'MAX_CLIPS_PER_VIDEO', 15))
        min_required = min(max_clips, max(1, getattr(self.config, 'MIN_CLIP_OUTPUT', 3)))
        target_goal = min(max_clips, max(min_required, getattr(self.config, 'TARGET_CLIP_COUNT', min_required)))

        base_threshold = getattr(self.config, 'MIN_VIRAL_SCORE', 0.10)
        relaxed_threshold = max(getattr(self.config, 'RELAXED_VIRAL_SCORE', 0.05), 0.0)
        fallback_threshold = max(getattr(self.config, 'FALLBACK_VIRAL_SCORE', 0.01), 0.0)

        print(f"   Thresholds: base={base_threshold}, relaxed={relaxed_threshold}, fallback={fallback_threshold}")
        print(f"   Goals: min={min_required}, target={target_goal}, max={max_clips}")

        seen_keys = set()

        def pick(threshold: float, limit: int) -> None:
            limit = min(limit, max_clips)
            if len(selected) >= limit:
                return
            for segment in candidates:
                if len(selected) >= limit:
                    break
                if not duration_ok(segment):
                    continue
                key = (round(segment['start'], 2), round(segment['end'], 2))
                if key in seen_keys:
                    continue
                effective_threshold = threshold
                if segment.get('is_fallback'):
                    effective_threshold = min(threshold, fallback_threshold)
                if segment.get('viral_score', 0) < effective_threshold:
                    continue
                if not self._is_distinct_segment(segment, selected):
                    continue
                selected.append(segment)
                seen_keys.add(key)

        # Progressive selection with decreasing thresholds
        for threshold, limit in (
            (base_threshold, target_goal),
            (relaxed_threshold, target_goal),
            (relaxed_threshold, max_clips),
            (fallback_threshold, max_clips),
            (0.0, max_clips),  # ZERO threshold as final attempt
        ):
            pick(threshold, limit)
            if len(selected) >= min_required:
                break
        
        print(f"   After threshold passes: {len(selected)} selected")

        # Force minimum if still not enough
        if len(selected) < min_required and candidates:
            print(f"   Forcing minimum output...")
            fallback_sorted = sorted(candidates, key=lambda item: item.get('viral_score', 0), reverse=True)
            for segment in fallback_sorted:
                if len(selected) >= min_required:
                    break
                if not duration_ok(segment):
                    continue
                key = (round(segment['start'], 2), round(segment['end'], 2))
                if key in seen_keys:
                    continue
                # More lenient overlap check for forced selection
                is_ok = True
                for existing in selected:
                    if self._calculate_overlap_ratio(existing, segment) > 0.85:
                        is_ok = False
                        break
                if not is_ok:
                    continue
                selected.append(segment)
                seen_keys.add(key)

        forced_min = max(1, getattr(self.config, 'FORCED_MIN_CLIP_OUTPUT', 3))
        if len(selected) < forced_min:
            forced = self._force_minimum_output(
                selected,
                candidates,
                fallback_segments,
                forced_min,
                min_duration,
                max_clips,
                seen_keys,
            )
            selected.extend(forced)

        print(f"   Final selection: {len(selected)} clips")
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
            'long': (28, 32),
            'extended': (40, 50)  # Extended duration for better context
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

    def _force_minimum_output(
        self,
        selected: List[Dict],
        candidates: List[Dict],
        fallback_segments: List[Dict],
        forced_min: int,
        min_duration: float,
        max_clips: int,
        seen_keys: set,
    ) -> List[Dict]:
        """Force output by picking best available segments when nothing passes thresholds."""
        # Priority: fallback > candidates > any scored segment
        pool = []
        
        # Add fallback segments first (they're designed for monologs)
        if fallback_segments:
            pool.extend([
                seg for seg in fallback_segments
                if seg.get('duration', 0) >= min_duration
            ])
        
        # Then add candidates that aren't in pool yet
        pool_keys = set((round(s['start'], 2), round(s['end'], 2)) for s in pool)
        for seg in candidates:
            key = (round(seg['start'], 2), round(seg['end'], 2))
            if key not in pool_keys and seg.get('duration', 0) >= min_duration:
                pool.append(seg)
                pool_keys.add(key)
        
        if not pool:
            print("⚠️ No segments available for forced output")
            return []

        forced = []
        target_total = min(max_clips, forced_min)
        
        # Sort by viral score but ensure variety by also considering time spread
        pool_sorted = sorted(pool, key=lambda seg: seg.get('viral_score', 0), reverse=True)

        for segment in pool_sorted:
            if len(selected) + len(forced) >= target_total:
                break
            key = (round(segment['start'], 2), round(segment['end'], 2))
            if key in seen_keys:
                continue
            if segment.get('duration', 0) < min_duration:
                continue
            
            # Relax distinct check for forced output - only check severe overlap
            is_ok = True
            for existing in selected + forced:
                overlap = self._calculate_overlap_ratio(existing, segment)
                if overlap > 0.8:  # More lenient: only reject if >80% overlap
                    is_ok = False
                    break
            
            if not is_ok:
                continue
                
            forced.append(segment)
            seen_keys.add(key)
        
        print(f"🔧 Forced {len(forced)} clips to meet minimum output")
        return forced
    
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
        Export a single clip using FFmpeg with ADVANCED GPU acceleration (NVIDIA CUDA)
        - Hardware-accelerated decoding (CUDA decoder)
        - CPU-based video filters (for compatibility) with GPU encoding
        - NVIDIA NVENC encoder with optimized settings
        - Supports both H.264 and H.265 (HEVC) codecs
        """
        output_path = os.path.join(output_dir, clip['filename'])
        
        # Build video filters for aspect ratio using instance resolution
        # Using CPU-based filters for better compatibility with GPU encoding
        video_filters = [
            f"scale=w={self.target_width}:h={self.target_height}:force_original_aspect_ratio=decrease",
            f"pad={self.target_width}:{self.target_height}:(ow-iw)/2:(oh-ih)/2:black"
        ]
        
        composite_filter = ','.join(video_filters)

        cmd = [
            'ffmpeg',
            '-hide_banner',  # Reduce verbose output
            '-loglevel', 'warning',  # Only show warnings and errors
        ]
        
        # Add hardware-accelerated DECODING if enabled
        if getattr(self.config, 'USE_GPU_ACCELERATION', True):
            cmd.extend([
                '-hwaccel', getattr(self.config, 'HWACCEL_DECODER', 'cuda'),
                '-hwaccel_output_format', 'nv12',  # Use standard output format for compatibility
            ])
            if hasattr(self.config, 'GPU_DEVICE'):
                cmd.extend([
                    '-hwaccel_device', str(getattr(self.config, 'GPU_DEVICE', 0))
                ])
        
        cmd.extend([
            '-i', self.video_path,
            '-ss', str(clip['start_seconds']),
            '-t', str(clip['duration']),
            '-vf', composite_filter
        ])
        
        # Add encoding parameters (ADVANCED GPU OPTIMIZATION)
        if getattr(self.config, 'USE_GPU_ACCELERATION', True) and self.config.VIDEO_CODEC in ['h264_nvenc', 'hevc_nvenc']:
            # NVIDIA NVENC encoder with advanced settings
            cmd.extend([
                '-c:v', self.config.VIDEO_CODEC,
                '-preset', getattr(self.config, 'NVENC_PRESET', 'medium'),  # slow/medium/fast
                '-rc', getattr(self.config, 'NVENC_RC_MODE', 'vbr'),  # Rate control mode
                '-b:v', self.target_bitrate,  # Target bitrate based on resolution
                '-maxrate', self.target_bitrate,  # Max bitrate
                '-bufsize', f"{int(int(self.target_bitrate.rstrip('M')) * 2)}M",  # Buffer size = 2x bitrate
                '-c:a', self.config.AUDIO_CODEC,
                '-b:a', self.config.AUDIO_BITRATE,
                '-y',  # Overwrite output file
                output_path
            ])
        else:
            # Fallback to CPU encoding if GPU not available
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', 'fast',  # CPU preset
                '-crf', '23',  # Quality (lower = better, 23 = good default)
                '-b:v', self.target_bitrate,
                '-c:a', self.config.AUDIO_CODEC,
                '-b:a', self.config.AUDIO_BITRATE,
                '-y',
                output_path
            ])
        
        # Run FFmpeg with GPU acceleration
        try:
            gpu_enabled = getattr(self.config, 'USE_GPU_ACCELERATION', True)
            gpu_filters = getattr(self.config, 'USE_GPU_FILTERS', False)
            print(f"   🎬 GPU Acceleration: {gpu_enabled} | GPU Filters: {gpu_filters} | Codec: {self.config.VIDEO_CODEC}")
            print(f"   🔧 Preset: {getattr(self.config, 'NVENC_PRESET', 'medium')} | Bitrate: {self.target_bitrate} | Resolution: {self.resolution}")
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"   ✅ Clip exported successfully: {os.path.basename(output_path)}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Error exporting clip: {e}")
            if e.stderr:
                print(f"   FFmpeg stderr: {e.stderr[:500]}")  # Show first 500 chars of error
            # Fallback to CPU if GPU fails
            print(f"   ⚠️  Fallback to CPU encoding...")
            return self._export_clip_cpu_fallback(clip, output_dir)
    
    def _export_clip_cpu_fallback(self, clip: Dict, output_dir: str) -> str:
        """
        Fallback CPU-based export if GPU fails
        """
        output_path = os.path.join(output_dir, clip['filename'])
        
        video_filters = [
            f"scale=w={self.target_width}:h={self.target_height}:force_original_aspect_ratio=decrease",
            f"pad={self.target_width}:{self.target_height}:(ow-iw)/2:(oh-ih)/2:black"
        ]
        composite_filter = ','.join(video_filters)
        
        cmd = [
            'ffmpeg',
            '-i', self.video_path,
            '-ss', str(clip['start_seconds']),
            '-t', str(clip['duration']),
            '-vf', composite_filter,
            '-c:v', 'libx264',
            '-b:v', self.target_bitrate,
            '-c:a', self.config.AUDIO_CODEC,
            '-b:a', self.config.AUDIO_BITRATE,
            '-preset', 'medium',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ CPU fallback also failed: {e}")
            return None
    
    def export_all_clips(self, clips: List[Dict], output_dir: str) -> List[str]:
        """
        Export all clips - PARALLEL VERSION
        Uses ThreadPoolExecutor for concurrent exports (GPU NVENC can handle multiple streams)
        """
        print(f"💾 Exporting {len(clips)} clips...")
        
        # Check if parallel export is enabled
        parallel_enabled = getattr(self.config, 'ENABLE_BATCH_EXPORT', True)
        max_workers = getattr(self.config, 'MAX_PARALLEL_EXPORTS', 2)
        
        if parallel_enabled and len(clips) > 1 and max_workers > 1:
            print(f"   ⚡ Parallel export enabled: {max_workers} concurrent exports")
            return self._export_parallel(clips, output_dir, max_workers)
        else:
            print(f"   📝 Sequential export mode")
            return self._export_sequential(clips, output_dir)
    
    def _export_parallel(self, clips: List[Dict], output_dir: str, max_workers: int) -> List[str]:
        """Parallel export using ThreadPoolExecutor"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        exported = []
        failed = []
        total = len(clips)
        
        def export_single(clip_data):
            """Worker function for single clip export"""
            idx, clip = clip_data
            try:
                output_path = self.export_clip(clip, output_dir)
                if output_path:
                    if clip.get('captions'):
                        self._write_caption_file(clip, output_dir)
                    # Write hook file for each clip (if timoty_hook exists)
                    self._write_hook_file(clip, output_dir)
                    return (idx, output_path, None)
                return (idx, None, "Export returned None")
            except Exception as e:
                return (idx, None, str(e))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all export jobs
            futures = {
                executor.submit(export_single, (idx, clip)): idx 
                for idx, clip in enumerate(clips)
            }
            
            # Process results as they complete
            completed = 0
            for future in as_completed(futures):
                completed += 1
                idx, output_path, error = future.result()
                
                if output_path:
                    exported.append(output_path)
                    print(f"   ✅ [{completed}/{total}] {clips[idx]['filename']} exported")
                else:
                    failed.append((idx, error))
                    print(f"   ❌ [{completed}/{total}] {clips[idx]['filename']} failed: {error}")
        
        if failed:
            print(f"   ⚠️ {len(failed)} clips failed to export")
        
        print(f"✅ Exported {len(exported)}/{total} clips successfully")
        return exported
    
    def _export_sequential(self, clips: List[Dict], output_dir: str) -> List[str]:
        """Sequential export (original method)"""
        exported = []
        delay = getattr(self.config, 'EXPORT_THROTTLE_SECONDS', 0)
        total = len(clips)
        
        for idx, clip in enumerate(clips):
            print(f"  [{idx + 1}/{total}] Exporting: {clip['filename']}")
            output_path = self.export_clip(clip, output_dir)
            
            if output_path:
                exported.append(output_path)
                if clip.get('captions'):
                    self._write_caption_file(clip, output_dir)
                # Write hook file for each clip (if timoty_hook exists)
                self._write_hook_file(clip, output_dir)
            
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
    
    def _write_hook_file(self, clip: Dict, output_dir: str) -> None:
        """
        Write hook text to a .txt file for each clip.
        The file is plain text, easily opened on Android devices.
        """
        hook_data = clip.get('timoty_hook')
        if not hook_data:
            return
        
        # Create filename: clip_001_hook.txt
        base_name = clip['filename'].rsplit('.', 1)[0]
        hook_filename = f"{base_name}_hook.txt"
        hook_path = os.path.join(output_dir, hook_filename)
        
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write(f"HOOK UNTUK: {clip['filename']}\n")
            f.write("=" * 50 + "\n\n")
            
            # Main hook text
            f.write("📢 HOOK TEXT:\n")
            f.write("-" * 30 + "\n")
            f.write(f"{hook_data.get('text', '')}\n\n")
            
            # Theme
            theme = hook_data.get('theme', 'default')
            f.write(f"🎯 TEMA: {theme.upper()}\n\n")
            
            # Power words
            power_words = hook_data.get('power_words', [])
            if power_words:
                f.write("⚡ POWER WORDS:\n")
                f.write(", ".join(power_words) + "\n\n")
            
            # Confidence
            confidence = hook_data.get('confidence', 0)
            f.write(f"📊 CONFIDENCE: {int(confidence * 100)}%\n\n")
            
            # Source fragment / context
            source = hook_data.get('source_fragment', '')
            if source:
                f.write("📝 KONTEKS SUMBER:\n")
                f.write("-" * 30 + "\n")
                f.write(f"{source}\n\n")
            
            # Clip info
            f.write("=" * 50 + "\n")
            f.write("INFO CLIP:\n")
            f.write(f"  Durasi: {clip['duration']:.1f} detik\n")
            f.write(f"  Waktu: {clip['start_time']} - {clip['end_time']}\n")
            f.write(f"  Viral Score: {clip.get('viral_score', 'N/A')}\n")
            f.write(f"  Kategori: {clip.get('category', 'N/A')}\n")
            f.write("=" * 50 + "\n")
        
        print(f"   📝 Hook file saved: {hook_filename}")

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

    def _smart_stitch_segments(self, selected: List[Dict], audio_segments: List[Dict], max_gap: float = 8.0) -> List[Dict]:
        """
        ENTERPRISE FEATURE: Smart Stitching
        Merge high-quality segments that are close together to form a cohesive narrative.
        Crucial for podcasts where thoughts are spread across pauses.
        """
        if len(selected) < 2:
            return selected
            
        print("   🧵 Running Smart Stitching (Enterprise Narrative Mode)...")
        stitched = []
        selected_sorted = sorted(selected, key=lambda x: x['start'])
        
        current_clip = selected_sorted[0]
        
        for next_clip in selected_sorted[1:]:
            # Check gap between clips
            gap = next_clip['start'] - current_clip['end']
            
            # Check conditions for stitching:
            # 1. Gap is small (continuation of thought)
            # 2. Both clips are same category/topic (simplified checking)
            # 3. Combined duration is not excessive
            
            can_merge = False
            if 0 < gap <= max_gap:
                combined_duration = next_clip['end'] - current_clip['start']
                if combined_duration <= 90: # Allow up to 90s for extended narrative
                    can_merge = True
            
            if can_merge:
                # Merge logic
                print(f"      🔗 Merging clips {current_clip['start']:.1f}s and {next_clip['start']:.1f}s (Gap: {gap:.1f}s)")
                
                # Fetch detailed text for the gap to ensure continuity
                gap_text = ""
                # (Simple linear search for gap text in audio segments could go here)
                
                current_clip['end'] = next_clip['end']
                current_clip['duration'] = current_clip['end'] - current_clip['start']
                current_clip['text'] = f"{current_clip['text']} ... {next_clip['text']}"
                current_clip['viral_score'] = max(current_clip['viral_score'], next_clip['viral_score'])
                current_clip['stitched'] = True
            else:
                stitched.append(current_clip)
                current_clip = next_clip
                
        stitched.append(current_clip)
        print(f"   ✅ Stitched {len(selected)} -> {len(stitched)} clips")
        return stitched

    def _polish_clip_boundaries(self, clips: List[Dict]) -> List[Dict]:
        """
        ENTERPRISE FEATURE: Boundary Polish
        Trim weak start words (conjunctions) and maximize semantic impact.
        Basically "auto-editing" the script.
        """
        weak_starters = [
            'dan ', 'and ', 'tapi ', 'but ', 'so ', 'jadi ', 'nah ', 'terus ', 
            'kemudian ', 'lalu ', 'maka ', 'sedangkan ', 'padahal '
        ]
        
        polished = []
        for clip in clips:
            text = clip.get('text', '').strip()
            text_lower = text.lower()
            
            # Check dirty start
            for starter in weak_starters:
                if text_lower.startswith(starter):
                    # In a real audio editor, we would trim the audio start time here.
                    # Since we rely on words, we try to estimate the shift.
                    # Avg word duration ~0.3s
                    shift_est = 0.3
                    if len(starter.strip()) > 4: shift_est = 0.5
                    
                    clip['start'] += shift_est
                    clip['duration'] -= shift_est
                    clip['text'] = text[len(starter):].strip().capitalize()
                    clip['polished'] = True
                    break
            
            polished.append(clip)
        return polished
