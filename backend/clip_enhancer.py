"""
Silence Remover & Vertical Format Module
Features:
- Remove silent pauses from clips (jump cut style)
- Auto-crop to 9:16 vertical format for TikTok/Reels
- Smart speaker tracking for vertical crop
"""

import os
import subprocess
import tempfile
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SilenceSegment:
    """Represents a silent segment in audio"""
    start: float
    end: float
    duration: float
    
    @property
    def is_significant(self) -> bool:
        """Check if silence is significant enough to remove"""
        return self.duration >= 0.3  # At least 300ms


@dataclass
class SpeakingSegment:
    """Represents a speaking segment (non-silent)"""
    start: float
    end: float
    duration: float


class SilenceRemover:
    """
    Remove silent pauses from video clips.
    Creates "jump cut" style videos with continuous speech.
    """
    
    def __init__(self, config):
        self.config = config
        
        # Silence detection settings
        self.silence_threshold_db = getattr(config, 'SILENCE_THRESHOLD_DB', -35)  # dB
        self.min_silence_duration = getattr(config, 'MIN_SILENCE_TO_REMOVE', 0.4)  # seconds
        self.min_speech_duration = getattr(config, 'MIN_SPEECH_DURATION', 0.2)  # seconds
        self.padding = getattr(config, 'SILENCE_PADDING', 0.05)  # Keep 50ms before/after speech
        
    def detect_silence(self, video_path: str) -> List[SilenceSegment]:
        """
        Detect silent segments in video using FFmpeg silencedetect filter.
        
        Returns list of SilenceSegment objects.
        """
        cmd = [
            'ffmpeg', '-i', video_path,
            '-af', f'silencedetect=noise={self.silence_threshold_db}dB:d={self.min_silence_duration}',
            '-f', 'null', '-'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = result.stderr
            silences = []
            
            # Parse FFmpeg silencedetect output
            lines = output.split('\n')
            current_start = None
            
            for line in lines:
                if 'silence_start:' in line:
                    try:
                        start_str = line.split('silence_start:')[1].strip().split()[0]
                        current_start = float(start_str)
                    except:
                        pass
                        
                elif 'silence_end:' in line and current_start is not None:
                    try:
                        parts = line.split('silence_end:')[1].strip().split()
                        end = float(parts[0])
                        duration = end - current_start
                        
                        silences.append(SilenceSegment(
                            start=current_start,
                            end=end,
                            duration=duration
                        ))
                        current_start = None
                    except:
                        pass
            
            return silences
            
        except Exception as e:
            print(f"⚠️ Silence detection failed: {e}")
            return []
    
    def get_speaking_segments(self, video_path: str, duration: float) -> List[SpeakingSegment]:
        """
        Get speaking (non-silent) segments from video.
        
        Returns list of SpeakingSegment objects.
        """
        silences = self.detect_silence(video_path)
        
        if not silences:
            # No silence detected - entire video is speech
            return [SpeakingSegment(start=0, end=duration, duration=duration)]
        
        speaking = []
        current_pos = 0.0
        
        for silence in silences:
            # Add speaking segment before this silence
            if silence.start > current_pos + self.min_speech_duration:
                # Add padding to keep natural flow
                seg_start = max(0, current_pos)
                seg_end = min(duration, silence.start + self.padding)
                
                speaking.append(SpeakingSegment(
                    start=seg_start,
                    end=seg_end,
                    duration=seg_end - seg_start
                ))
            
            # Move position to end of silence (with padding)
            current_pos = max(current_pos, silence.end - self.padding)
        
        # Add final speaking segment
        if current_pos < duration - self.min_speech_duration:
            speaking.append(SpeakingSegment(
                start=current_pos,
                end=duration,
                duration=duration - current_pos
            ))
        
        return speaking
    
    def remove_silence(self, input_path: str, output_path: str, 
                       use_gpu: bool = True) -> Tuple[bool, Dict]:
        """
        Remove silent segments from video.
        
        Args:
            input_path: Source video path
            output_path: Output video path
            use_gpu: Use GPU acceleration if available
            
        Returns:
            (success, stats) tuple
        """
        # Get video duration first
        duration = self._get_duration(input_path)
        if duration <= 0:
            return False, {'error': 'Could not get video duration'}
        
        # Detect speaking segments
        print(f"   🔍 Detecting speech segments...")
        speaking = self.get_speaking_segments(input_path, duration)
        
        if not speaking:
            return False, {'error': 'No speaking segments detected'}
        
        # Calculate stats
        original_duration = duration
        new_duration = sum(seg.duration for seg in speaking)
        removed_duration = original_duration - new_duration
        
        print(f"   📊 Original: {original_duration:.1f}s → New: {new_duration:.1f}s")
        print(f"   ✂️  Removed: {removed_duration:.1f}s of silence ({len(speaking)} segments)")
        
        # If minimal silence, just copy
        if removed_duration < 0.5:
            print(f"   ℹ️  Minimal silence detected, keeping original")
            import shutil
            shutil.copy(input_path, output_path)
            return True, {
                'original_duration': original_duration,
                'new_duration': original_duration,
                'removed_duration': 0,
                'segments': 1
            }
        
        # Build FFmpeg complex filter to concatenate speaking segments
        success = self._concatenate_segments(input_path, output_path, speaking, use_gpu)
        
        return success, {
            'original_duration': original_duration,
            'new_duration': new_duration,
            'removed_duration': removed_duration,
            'segments': len(speaking),
            'compression_ratio': new_duration / original_duration if original_duration > 0 else 1
        }
    
    def _concatenate_segments(self, input_path: str, output_path: str, 
                              segments: List[SpeakingSegment], use_gpu: bool) -> bool:
        """Concatenate speaking segments using FFmpeg"""
        
        # Create filter complex for segment extraction and concat
        filter_parts = []
        concat_inputs = []
        
        for i, seg in enumerate(segments):
            # Trim each segment
            filter_parts.append(
                f"[0:v]trim=start={seg.start}:end={seg.end},setpts=PTS-STARTPTS[v{i}];"
            )
            filter_parts.append(
                f"[0:a]atrim=start={seg.start}:end={seg.end},asetpts=PTS-STARTPTS[a{i}];"
            )
            concat_inputs.append(f"[v{i}][a{i}]")
        
        # Concat all segments
        filter_complex = ''.join(filter_parts)
        filter_complex += f"{''.join(concat_inputs)}concat=n={len(segments)}:v=1:a=1[outv][outa]"
        
        # Build FFmpeg command
        cmd = ['ffmpeg', '-y', '-i', input_path]
        
        # GPU acceleration
        if use_gpu and getattr(self.config, 'USE_GPU_ACCELERATION', False):
            cmd.extend(['-hwaccel', 'cuda'])
        
        cmd.extend([
            '-filter_complex', filter_complex,
            '-map', '[outv]', '-map', '[outa]'
        ])
        
        # Video codec
        if use_gpu and getattr(self.config, 'USE_GPU_ACCELERATION', False):
            cmd.extend(['-c:v', getattr(self.config, 'VIDEO_CODEC', 'h264_nvenc')])
            cmd.extend(['-preset', getattr(self.config, 'NVENC_PRESET', 'p4')])
        else:
            cmd.extend(['-c:v', 'libx264', '-preset', 'fast'])
        
        cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        cmd.append(output_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0 and os.path.exists(output_path)
        except Exception as e:
            print(f"   ❌ Concatenation failed: {e}")
            return False
    
    def _get_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except:
            return 0


class VerticalFormatter:
    """
    Convert videos to 9:16 vertical format for TikTok/Reels.
    Features smart cropping with speaker detection.
    """
    
    # Preset formats
    FORMATS = {
        '9:16': {'width': 1080, 'height': 1920, 'name': 'TikTok/Reels'},
        '4:5': {'width': 1080, 'height': 1350, 'name': 'Instagram Feed'},
        '1:1': {'width': 1080, 'height': 1080, 'name': 'Square'},
        '16:9': {'width': 1920, 'height': 1080, 'name': 'YouTube/Landscape'},
    }
    
    def __init__(self, config):
        self.config = config
        self.default_format = getattr(config, 'DEFAULT_VERTICAL_FORMAT', '9:16')
        
    def convert_to_vertical(self, input_path: str, output_path: str,
                           format_ratio: str = '9:16',
                           crop_position: str = 'center',
                           use_gpu: bool = True) -> Tuple[bool, Dict]:
        """
        Convert video to vertical format.
        
        Args:
            input_path: Source video path
            output_path: Output video path
            format_ratio: Target ratio ('9:16', '4:5', '1:1')
            crop_position: Crop position ('center', 'left', 'right', 'auto')
            use_gpu: Use GPU acceleration
            
        Returns:
            (success, metadata) tuple
        """
        if format_ratio not in self.FORMATS:
            format_ratio = '9:16'
        
        target = self.FORMATS[format_ratio]
        target_w = target['width']
        target_h = target['height']
        
        print(f"   🎬 Converting to {format_ratio} ({target['name']})")
        
        # Get source dimensions
        src_w, src_h = self._get_dimensions(input_path)
        if src_w <= 0 or src_h <= 0:
            return False, {'error': 'Could not get video dimensions'}
        
        # Calculate crop parameters
        crop_params = self._calculate_crop(src_w, src_h, target_w, target_h, crop_position)
        
        # Build FFmpeg command
        success = self._apply_vertical_crop(
            input_path, output_path, crop_params, target_w, target_h, use_gpu
        )
        
        return success, {
            'format': format_ratio,
            'format_name': target['name'],
            'source_size': f'{src_w}x{src_h}',
            'target_size': f'{target_w}x{target_h}',
            'crop_position': crop_position
        }
    
    def _get_dimensions(self, video_path: str) -> Tuple[int, int]:
        """Get video dimensions using ffprobe"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(result.stdout)
            stream = data['streams'][0]
            return int(stream['width']), int(stream['height'])
        except:
            return 0, 0
    
    def _calculate_crop(self, src_w: int, src_h: int, 
                       target_w: int, target_h: int,
                       position: str) -> Dict:
        """
        Calculate crop parameters to fit target aspect ratio.
        
        Returns dict with crop_w, crop_h, crop_x, crop_y
        """
        src_ratio = src_w / src_h
        target_ratio = target_w / target_h
        
        if src_ratio > target_ratio:
            # Source is wider - crop sides
            crop_h = src_h
            crop_w = int(src_h * target_ratio)
            crop_y = 0
            
            if position == 'center':
                crop_x = (src_w - crop_w) // 2
            elif position == 'left':
                crop_x = 0
            elif position == 'right':
                crop_x = src_w - crop_w
            else:  # auto - default to center
                crop_x = (src_w - crop_w) // 2
        else:
            # Source is taller - crop top/bottom
            crop_w = src_w
            crop_h = int(src_w / target_ratio)
            crop_x = 0
            crop_y = (src_h - crop_h) // 2
        
        return {
            'crop_w': crop_w,
            'crop_h': crop_h,
            'crop_x': crop_x,
            'crop_y': crop_y
        }
    
    def _apply_vertical_crop(self, input_path: str, output_path: str,
                             crop: Dict, target_w: int, target_h: int,
                             use_gpu: bool) -> bool:
        """Apply crop and scale to target dimensions"""
        
        # Build filter
        if use_gpu and getattr(self.config, 'USE_GPU_FILTERS', False):
            # GPU filter chain
            vf = (
                f"crop={crop['crop_w']}:{crop['crop_h']}:{crop['crop_x']}:{crop['crop_y']},"
                f"scale_cuda={target_w}:{target_h}"
            )
        else:
            # CPU filter chain
            vf = (
                f"crop={crop['crop_w']}:{crop['crop_h']}:{crop['crop_x']}:{crop['crop_y']},"
                f"scale={target_w}:{target_h}"
            )
        
        # Build command
        cmd = ['ffmpeg', '-y']
        
        # GPU decode
        if use_gpu and getattr(self.config, 'USE_GPU_ACCELERATION', False):
            cmd.extend(['-hwaccel', 'cuda'])
        
        cmd.extend(['-i', input_path])
        cmd.extend(['-vf', vf])
        
        # Video codec
        if use_gpu and getattr(self.config, 'USE_GPU_ACCELERATION', False):
            cmd.extend(['-c:v', getattr(self.config, 'VIDEO_CODEC', 'h264_nvenc')])
            cmd.extend(['-preset', getattr(self.config, 'NVENC_PRESET', 'p4')])
            cmd.extend(['-b:v', getattr(self.config, 'VIDEO_BITRATE', '4M')])
        else:
            cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '23'])
        
        cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        cmd.append(output_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0 and os.path.exists(output_path)
        except Exception as e:
            print(f"   ❌ Vertical conversion failed: {e}")
            return False


class ClipEnhancer:
    """
    Combines silence removal and vertical formatting.
    Creates TikTok/Reels-ready clips.
    """
    
    def __init__(self, config):
        self.config = config
        self.silence_remover = SilenceRemover(config)
        self.vertical_formatter = VerticalFormatter(config)
    
    def enhance_clip(self, input_path: str, output_path: str,
                     remove_silence: bool = True,
                     vertical_format: Optional[str] = None,
                     crop_position: str = 'center',
                     use_gpu: bool = True) -> Tuple[bool, Dict]:
        """
        Enhance a clip with silence removal and vertical formatting.
        
        Args:
            input_path: Source clip path
            output_path: Output clip path
            remove_silence: Remove silent pauses
            vertical_format: Target format ('9:16', '4:5', '1:1', None for no change)
            crop_position: Crop position for vertical ('center', 'left', 'right')
            use_gpu: Use GPU acceleration
            
        Returns:
            (success, metadata) tuple
        """
        temp_files = []
        current_input = input_path
        metadata = {'steps': []}
        
        try:
            # Step 1: Remove silence if requested
            if remove_silence:
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                temp_files.append(temp_path)
                
                print(f"   ✂️ Step 1: Removing silence...")
                success, silence_stats = self.silence_remover.remove_silence(
                    current_input, temp_path, use_gpu
                )
                
                if success:
                    current_input = temp_path
                    metadata['steps'].append({'silence_removal': silence_stats})
                    metadata['silence_removed'] = True
                else:
                    print(f"   ⚠️ Silence removal failed, continuing...")
                    metadata['silence_removed'] = False
            
            # Step 2: Convert to vertical if requested
            if vertical_format:
                print(f"   📱 Step 2: Converting to {vertical_format}...")
                success, format_stats = self.vertical_formatter.convert_to_vertical(
                    current_input, output_path, vertical_format, crop_position, use_gpu
                )
                
                if success:
                    metadata['steps'].append({'vertical_format': format_stats})
                    metadata['format'] = vertical_format
                    return True, metadata
                else:
                    return False, {'error': 'Vertical conversion failed'}
            else:
                # No vertical format - just copy final result
                if current_input != input_path:
                    import shutil
                    shutil.move(current_input, output_path)
                    temp_files.remove(current_input)
                else:
                    import shutil
                    shutil.copy(current_input, output_path)
                
                return True, metadata
                
        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
    
    def batch_enhance(self, clips: List[Dict], output_dir: str,
                      remove_silence: bool = True,
                      vertical_format: Optional[str] = None,
                      use_gpu: bool = True) -> List[Dict]:
        """
        Enhance multiple clips.
        
        Args:
            clips: List of clip dicts with 'path' key
            output_dir: Output directory
            remove_silence: Remove silent pauses
            vertical_format: Target format
            use_gpu: Use GPU acceleration
            
        Returns:
            List of enhanced clip metadata
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, clip in enumerate(clips):
            input_path = clip.get('path')
            if not input_path or not os.path.exists(input_path):
                results.append({'error': 'Invalid input path', 'clip': clip})
                continue
            
            # Generate output filename
            base_name = os.path.basename(input_path)
            name, ext = os.path.splitext(base_name)
            
            suffix = ""
            if remove_silence:
                suffix += "_nosilence"
            if vertical_format:
                suffix += f"_{vertical_format.replace(':', 'x')}"
            
            output_name = f"{name}{suffix}{ext}"
            output_path = os.path.join(output_dir, output_name)
            
            print(f"\n🎬 Enhancing clip {i+1}/{len(clips)}: {base_name}")
            
            success, metadata = self.enhance_clip(
                input_path, output_path,
                remove_silence=remove_silence,
                vertical_format=vertical_format,
                use_gpu=use_gpu
            )
            
            results.append({
                'input': input_path,
                'output': output_path if success else None,
                'success': success,
                **metadata
            })
        
        return results


# Convenience functions
def remove_silence_from_clip(input_path: str, output_path: str, config) -> Tuple[bool, Dict]:
    """Remove silence from a single clip"""
    remover = SilenceRemover(config)
    return remover.remove_silence(input_path, output_path)


def convert_to_tiktok(input_path: str, output_path: str, config,
                      crop_position: str = 'center') -> Tuple[bool, Dict]:
    """Convert clip to TikTok 9:16 format"""
    formatter = VerticalFormatter(config)
    return formatter.convert_to_vertical(input_path, output_path, '9:16', crop_position)


def create_tiktok_ready_clip(input_path: str, output_path: str, config,
                             remove_silence: bool = True) -> Tuple[bool, Dict]:
    """Create TikTok-ready clip with silence removed and 9:16 format"""
    enhancer = ClipEnhancer(config)
    return enhancer.enhance_clip(
        input_path, output_path,
        remove_silence=remove_silence,
        vertical_format='9:16',
        use_gpu=getattr(config, 'USE_GPU_ACCELERATION', True)
    )
