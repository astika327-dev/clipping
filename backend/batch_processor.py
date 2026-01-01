"""
Batch Processor Module for AI Video Clipper
Handles parallel processing of multiple clips with GPU optimization

Features:
- GPU-accelerated parallel clip export
- Smart queue management
- Memory-aware batch sizing
- Progress tracking
- Error recovery
"""

import os
import time
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Callable, Optional, Tuple
from dataclasses import dataclass, field
import subprocess
import json

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False


@dataclass
class ClipTask:
    """Represents a single clip export task"""
    clip_id: int
    input_path: str
    output_path: str
    start_time: float
    end_time: float
    options: Dict = field(default_factory=dict)
    status: str = 'pending'  # pending, processing, completed, failed
    error: Optional[str] = None
    progress: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def processing_time(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class BatchJob:
    """Represents a batch of clip tasks"""
    job_id: str
    tasks: List[ClipTask]
    created_at: float = field(default_factory=time.time)
    status: str = 'pending'  # pending, processing, completed, failed, cancelled
    completed_count: int = 0
    failed_count: int = 0
    
    @property
    def total_count(self) -> int:
        return len(self.tasks)
    
    @property
    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        return (self.completed_count + self.failed_count) / self.total_count * 100
    
    @property
    def is_complete(self) -> bool:
        return (self.completed_count + self.failed_count) >= self.total_count


class BatchProcessor:
    """
    High-performance batch processor for parallel clip exports.
    Optimized for GPU-accelerated NVENC encoding.
    """
    
    def __init__(self, config, gpu_optimizer=None):
        self.config = config
        self.gpu_optimizer = gpu_optimizer
        
        # Determine optimal worker count
        self.max_workers = self._get_optimal_workers()
        
        # Task queue and tracking
        self.task_queue: queue.Queue = queue.Queue()
        self.active_jobs: Dict[str, BatchJob] = {}
        self.completed_jobs: Dict[str, BatchJob] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Stats
        self.total_clips_processed = 0
        self.total_processing_time = 0.0
        self.avg_clip_time = 0.0
        
        print(f"   🔧 BatchProcessor initialized with {self.max_workers} parallel workers")
    
    def _get_optimal_workers(self) -> int:
        """Determine optimal number of parallel workers"""
        # From config
        config_workers = getattr(self.config, 'MAX_PARALLEL_EXPORTS', 4)
        
        # From GPU optimizer if available
        if self.gpu_optimizer and self.gpu_optimizer.profile:
            gpu_workers = self.gpu_optimizer.profile.max_parallel_exports
            return min(config_workers, gpu_workers)
        
        # CPU-based fallback
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        return min(config_workers, max(2, cpu_count // 2))
    
    def create_batch_job(self, job_id: str, clips: List[Dict], input_video: str, output_dir: str) -> BatchJob:
        """
        Create a batch job from a list of clips.
        
        Args:
            job_id: Unique job identifier
            clips: List of clip dictionaries with start, end, options
            input_video: Path to source video
            output_dir: Directory for output clips
            
        Returns:
            BatchJob instance
        """
        tasks = []
        
        for i, clip in enumerate(clips):
            # Generate output filename
            clip_num = i + 1
            score = clip.get('viral_score', 0)
            duration = clip.get('end', 0) - clip.get('start', 0)
            
            output_filename = f"clip_{clip_num:02d}_score{int(score*100):03d}_{duration:.0f}s.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            task = ClipTask(
                clip_id=clip_num,
                input_path=input_video,
                output_path=output_path,
                start_time=clip.get('start', 0),
                end_time=clip.get('end', 0),
                options={
                    'hook_text': clip.get('hook_text', ''),
                    'hook_duration': clip.get('hook_duration', 0),
                    'viral_score': score,
                    'resolution': clip.get('resolution', getattr(self.config, 'DEFAULT_RESOLUTION', '1080p')),
                    **clip.get('export_options', {})
                }
            )
            tasks.append(task)
        
        batch_job = BatchJob(job_id=job_id, tasks=tasks)
        
        with self._lock:
            self.active_jobs[job_id] = batch_job
        
        print(f"   📦 Created batch job '{job_id}' with {len(tasks)} clips")
        return batch_job
    
    def process_batch(self, 
                      job_id: str, 
                      export_function: Callable,
                      progress_callback: Optional[Callable] = None) -> BatchJob:
        """
        Process a batch job using parallel workers.
        
        Args:
            job_id: ID of the batch job to process
            export_function: Function to call for each clip export
                            Signature: export_function(task: ClipTask), returns bool
            progress_callback: Optional callback for progress updates
                              Signature: callback(job_id, completed, total, current_task)
        
        Returns:
            The completed BatchJob
        """
        with self._lock:
            if job_id not in self.active_jobs:
                raise ValueError(f"Job '{job_id}' not found")
            batch_job = self.active_jobs[job_id]
        
        batch_job.status = 'processing'
        start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"🚀 BATCH PROCESSING: {batch_job.total_count} clips")
        print(f"   Workers: {self.max_workers}")
        print(f"{'='*60}")
        
        # Use ThreadPoolExecutor for I/O bound FFmpeg operations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in batch_job.tasks:
                task.status = 'pending'
                future = executor.submit(self._process_single_task, task, export_function)
                future_to_task[future] = task
            
            # Process completed tasks
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                try:
                    success = future.result()
                    if success:
                        batch_job.completed_count += 1
                        task.status = 'completed'
                        print(f"   ✅ Clip {task.clip_id}/{batch_job.total_count}: {os.path.basename(task.output_path)}")
                    else:
                        batch_job.failed_count += 1
                        task.status = 'failed'
                        print(f"   ❌ Clip {task.clip_id}/{batch_job.total_count}: FAILED")
                except Exception as e:
                    batch_job.failed_count += 1
                    task.status = 'failed'
                    task.error = str(e)
                    print(f"   ❌ Clip {task.clip_id}/{batch_job.total_count}: {e}")
                
                # Progress callback
                if progress_callback:
                    try:
                        progress_callback(
                            job_id,
                            batch_job.completed_count + batch_job.failed_count,
                            batch_job.total_count,
                            task
                        )
                    except:
                        pass
        
        # Finalize job
        total_time = time.time() - start_time
        batch_job.status = 'completed' if batch_job.failed_count == 0 else 'completed_with_errors'
        
        # Update stats
        self.total_clips_processed += batch_job.completed_count
        self.total_processing_time += total_time
        if self.total_clips_processed > 0:
            self.avg_clip_time = self.total_processing_time / self.total_clips_processed
        
        # Move to completed
        with self._lock:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            self.completed_jobs[job_id] = batch_job
        
        print(f"\n{'='*60}")
        print(f"✅ BATCH COMPLETE")
        print(f"   Completed: {batch_job.completed_count}/{batch_job.total_count}")
        print(f"   Failed: {batch_job.failed_count}")
        print(f"   Total Time: {total_time:.1f}s")
        print(f"   Avg per Clip: {total_time/batch_job.total_count:.1f}s")
        print(f"{'='*60}\n")
        
        return batch_job
    
    def _process_single_task(self, task: ClipTask, export_function: Callable) -> bool:
        """Process a single clip task"""
        task.status = 'processing'
        task.started_at = time.time()
        
        try:
            success = export_function(task)
            task.completed_at = time.time()
            return success
        except Exception as e:
            task.error = str(e)
            task.completed_at = time.time()
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a batch job"""
        with self._lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
            elif job_id in self.completed_jobs:
                job = self.completed_jobs[job_id]
            else:
                return None
        
        return {
            'job_id': job.job_id,
            'status': job.status,
            'total': job.total_count,
            'completed': job.completed_count,
            'failed': job.failed_count,
            'progress': job.progress,
            'tasks': [
                {
                    'clip_id': t.clip_id,
                    'status': t.status,
                    'output': os.path.basename(t.output_path),
                    'duration': t.duration,
                    'processing_time': t.processing_time,
                    'error': t.error
                }
                for t in job.tasks
            ]
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running batch job"""
        with self._lock:
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = 'cancelled'
                return True
        return False
    
    def get_stats(self) -> Dict:
        """Get batch processor statistics"""
        return {
            'max_workers': self.max_workers,
            'total_clips_processed': self.total_clips_processed,
            'total_processing_time': round(self.total_processing_time, 2),
            'avg_clip_time': round(self.avg_clip_time, 2),
            'active_jobs': len(self.active_jobs),
            'completed_jobs': len(self.completed_jobs),
        }


class GPUAwareExporter:
    """
    GPU-aware video exporter that builds optimal FFmpeg commands
    for NVENC encoding with smart fallback to CPU.
    """
    
    def __init__(self, config, gpu_optimizer=None):
        self.config = config
        self.gpu_optimizer = gpu_optimizer
        self.use_gpu = self._check_gpu_available()
        
        # Build FFmpeg base command
        self.ffmpeg_base = self._build_base_command()
        
        print(f"   🎬 GPUAwareExporter: {'GPU (NVENC)' if self.use_gpu else 'CPU'} mode")
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU encoding is available"""
        if not getattr(self.config, 'USE_GPU_ACCELERATION', True):
            return False
        
        # Check for NVENC support
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'h264_nvenc' in result.stdout
        except:
            return False
    
    def _build_base_command(self) -> List[str]:
        """Build base FFmpeg command with optimal settings"""
        cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning']
        
        if self.use_gpu:
            # GPU acceleration flags
            hwaccel = getattr(self.config, 'HWACCEL_DECODER', 'cuda')
            cmd.extend(['-hwaccel', hwaccel])
            
            if hwaccel == 'cuda':
                # Keep frames on GPU
                cmd.extend(['-hwaccel_output_format', 'cuda'])
        
        return cmd
    
    def build_export_command(self, task: ClipTask) -> List[str]:
        """
        Build complete FFmpeg command for a clip export task.
        
        Args:
            task: ClipTask containing input/output paths and options
            
        Returns:
            Complete FFmpeg command as list
        """
        cmd = self.ffmpeg_base.copy()
        
        # Input with seek
        cmd.extend(['-ss', str(task.start_time)])
        cmd.extend(['-i', task.input_path])
        cmd.extend(['-t', str(task.duration)])
        
        # Video codec and settings
        if self.use_gpu:
            codec = getattr(self.config, 'VIDEO_CODEC', 'h264_nvenc')
            preset = getattr(self.config, 'NVENC_PRESET', 'medium')
            
            cmd.extend(['-c:v', codec])
            cmd.extend(['-preset', preset])
            
            # NVENC specific options
            rc_mode = getattr(self.config, 'NVENC_RC_MODE', 'vbr')
            if rc_mode == 'vbr':
                cmd.extend(['-rc', 'vbr'])
                cmd.extend(['-cq', str(getattr(self.config, 'NVENC_QUALITY', 23))])
            elif rc_mode == 'cbr':
                cmd.extend(['-rc', 'cbr'])
        else:
            # CPU encoding
            preset = getattr(self.config, 'CPU_PRESET', 'fast')
            cmd.extend(['-c:v', 'libx264'])
            cmd.extend(['-preset', preset])
        
        # Bitrate
        bitrate = task.options.get('bitrate', getattr(self.config, 'VIDEO_BITRATE', '4M'))
        cmd.extend(['-b:v', bitrate])
        
        # Resolution
        resolution = task.options.get('resolution', getattr(self.config, 'DEFAULT_RESOLUTION', '1080p'))
        presets = getattr(self.config, 'RESOLUTION_PRESETS', {})
        if resolution in presets:
            width = presets[resolution]['width']
            height = presets[resolution]['height']
            
            if self.use_gpu and getattr(self.config, 'USE_GPU_FILTERS', False):
                # GPU scaling
                cmd.extend(['-vf', f'scale_cuda={width}:{height}'])
            else:
                # CPU scaling
                cmd.extend(['-vf', f'scale={width}:{height}'])
        
        # Audio
        cmd.extend(['-c:a', getattr(self.config, 'AUDIO_CODEC', 'aac')])
        cmd.extend(['-b:a', getattr(self.config, 'AUDIO_BITRATE', '192k')])
        
        # Threading for CPU encoding
        if not self.use_gpu:
            threads = getattr(self.config, 'FFMPEG_THREADS', 4)
            cmd.extend(['-threads', str(threads)])
        
        # Output
        cmd.append(task.output_path)
        
        return cmd
    
    def export_clip(self, task: ClipTask) -> bool:
        """
        Export a single clip using optimized FFmpeg command.
        
        Args:
            task: ClipTask to export
            
        Returns:
            True if successful, False otherwise
        """
        cmd = self.build_export_command(task)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0 and os.path.exists(task.output_path):
                # Verify file is valid
                file_size = os.path.getsize(task.output_path)
                if file_size > 1000:  # At least 1KB
                    return True
                else:
                    task.error = "Output file too small"
                    return False
            else:
                task.error = result.stderr.decode('utf-8', errors='ignore')[:500]
                return False
                
        except subprocess.TimeoutExpired:
            task.error = "Export timeout"
            return False
        except Exception as e:
            task.error = str(e)
            return False


def create_batch_processor(config, gpu_optimizer=None) -> Tuple[BatchProcessor, GPUAwareExporter]:
    """
    Factory function to create BatchProcessor and GPUAwareExporter.
    
    Returns:
        Tuple of (BatchProcessor, GPUAwareExporter)
    """
    exporter = GPUAwareExporter(config, gpu_optimizer)
    processor = BatchProcessor(config, gpu_optimizer)
    
    return processor, exporter
