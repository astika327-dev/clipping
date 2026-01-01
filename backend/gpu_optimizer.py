"""
GPU Optimizer Module for AWS EC2 g4dn Instances
Optimizes AI Video Clipper for NVIDIA T4 GPU (16GB VRAM)

Features:
- Auto-detect GPU type and capabilities
- Optimal batch sizing based on VRAM
- CUDA memory pool management
- Multi-GPU support
- Real-time GPU health monitoring
- AWS-specific optimizations
"""

import os
import subprocess
import json
import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache

# Try to import GPU libraries
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except (ImportError, Exception):
    pynvml = None
    NVML_AVAILABLE = False


@dataclass
class GPUInfo:
    """GPU information container"""
    index: int
    name: str
    total_memory_mb: int
    free_memory_mb: int
    used_memory_mb: int
    temperature: int
    utilization: int
    driver_version: str
    cuda_version: str
    compute_capability: Tuple[int, int]
    
    @property
    def memory_utilization(self) -> float:
        return (self.used_memory_mb / self.total_memory_mb) * 100 if self.total_memory_mb > 0 else 0


@dataclass
class GPUProfile:
    """Optimized settings profile for a specific GPU"""
    name: str
    whisper_model: str
    whisper_compute_type: str
    whisper_beam_size: int
    max_parallel_exports: int
    video_bitrate: str
    nvenc_preset: str
    max_batch_size: int
    use_tensorrt: bool
    optimal_workers: int
    description: str


# Pre-defined GPU profiles
GPU_PROFILES = {
    # AWS g4dn instances (NVIDIA T4)
    'Tesla T4': GPUProfile(
        name='Tesla T4',
        whisper_model='large-v3',
        whisper_compute_type='float16',
        whisper_beam_size=3,
        max_parallel_exports=4,
        video_bitrate='4M',
        nvenc_preset='medium',
        max_batch_size=8,
        use_tensorrt=True,
        optimal_workers=4,
        description='AWS g4dn instance - NVIDIA T4 16GB'
    ),
    # AWS p3 instances (NVIDIA V100)
    'Tesla V100': GPUProfile(
        name='Tesla V100',
        whisper_model='large-v3',
        whisper_compute_type='float16',
        whisper_beam_size=5,
        max_parallel_exports=6,
        video_bitrate='6M',
        nvenc_preset='slow',
        max_batch_size=16,
        use_tensorrt=True,
        optimal_workers=8,
        description='AWS p3 instance - NVIDIA V100 16/32GB'
    ),
    # AWS g5 instances (NVIDIA A10G)
    'NVIDIA A10G': GPUProfile(
        name='NVIDIA A10G',
        whisper_model='large-v3',
        whisper_compute_type='float16',
        whisper_beam_size=5,
        max_parallel_exports=6,
        video_bitrate='6M',
        nvenc_preset='medium',
        max_batch_size=16,
        use_tensorrt=True,
        optimal_workers=6,
        description='AWS g5 instance - NVIDIA A10G 24GB'
    ),
    # Consumer GPUs
    'NVIDIA GeForce RTX 3060': GPUProfile(
        name='NVIDIA GeForce RTX 3060',
        whisper_model='large-v3',
        whisper_compute_type='float16',
        whisper_beam_size=3,
        max_parallel_exports=3,
        video_bitrate='4M',
        nvenc_preset='medium',
        max_batch_size=6,
        use_tensorrt=False,
        optimal_workers=3,
        description='RTX 3060 12GB - Consumer GPU'
    ),
    'NVIDIA GeForce RTX 4090': GPUProfile(
        name='NVIDIA GeForce RTX 4090',
        whisper_model='large-v3',
        whisper_compute_type='float16',
        whisper_beam_size=5,
        max_parallel_exports=8,
        video_bitrate='8M',
        nvenc_preset='slow',
        max_batch_size=24,
        use_tensorrt=True,
        optimal_workers=8,
        description='RTX 4090 24GB - High-end Consumer GPU'
    ),
    # Default fallback
    'default': GPUProfile(
        name='Generic GPU',
        whisper_model='medium',
        whisper_compute_type='int8_float16',
        whisper_beam_size=2,
        max_parallel_exports=2,
        video_bitrate='2M',
        nvenc_preset='fast',
        max_batch_size=4,
        use_tensorrt=False,
        optimal_workers=2,
        description='Generic GPU with ~8GB VRAM'
    )
}


class GPUOptimizer:
    """
    Main GPU Optimizer class for AI Video Clipper.
    Handles GPU detection, profiling, and optimization.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for GPU optimizer"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.gpus: List[GPUInfo] = []
        self.primary_gpu: Optional[GPUInfo] = None
        self.profile: Optional[GPUProfile] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False
        self._gpu_stats_history: List[Dict] = []
        
        # Detect GPUs on initialization
        self._detect_gpus()
        self._select_profile()
        
        print(f"\n{'='*60}")
        print("🔥 GPU OPTIMIZER INITIALIZED")
        print(f"{'='*60}")
        if self.primary_gpu:
            print(f"   GPU: {self.primary_gpu.name}")
            print(f"   VRAM: {self.primary_gpu.total_memory_mb}MB")
            print(f"   Driver: {self.primary_gpu.driver_version}")
            print(f"   CUDA: {self.primary_gpu.cuda_version}")
            print(f"\n   Profile: {self.profile.description}")
            print(f"   Whisper Model: {self.profile.whisper_model} ({self.profile.whisper_compute_type})")
            print(f"   Parallel Exports: {self.profile.max_parallel_exports}")
            print(f"   Batch Size: {self.profile.max_batch_size}")
        else:
            print("   ⚠️ No GPU detected - using CPU fallback")
        print(f"{'='*60}\n")
    
    def _detect_gpus(self) -> None:
        """Detect all available GPUs using PyTorch and NVML"""
        self.gpus = []
        
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            print("   ⚠️ CUDA not available")
            return
        
        gpu_count = torch.cuda.device_count()
        print(f"   🔍 Detecting {gpu_count} GPU(s)...")
        
        for i in range(gpu_count):
            try:
                # Get basic info from PyTorch
                props = torch.cuda.get_device_properties(i)
                name = props.name
                total_memory = props.total_memory // (1024 * 1024)  # MB
                
                # Get more detailed info from NVML if available
                free_memory = 0
                used_memory = 0
                temperature = 0
                utilization = 0
                driver_version = "Unknown"
                cuda_version = torch.version.cuda or "Unknown"
                
                if NVML_AVAILABLE:
                    try:
                        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        free_memory = mem_info.free // (1024 * 1024)
                        used_memory = mem_info.used // (1024 * 1024)
                        temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        utilization = util.gpu
                        driver_version = pynvml.nvmlSystemGetDriverVersion()
                        if isinstance(driver_version, bytes):
                            driver_version = driver_version.decode('utf-8')
                    except:
                        # Estimate from PyTorch
                        free_memory = total_memory
                        used_memory = 0
                else:
                    # Estimate from PyTorch
                    free_memory = total_memory
                    used_memory = 0
                
                gpu_info = GPUInfo(
                    index=i,
                    name=name,
                    total_memory_mb=total_memory,
                    free_memory_mb=free_memory,
                    used_memory_mb=used_memory,
                    temperature=temperature,
                    utilization=utilization,
                    driver_version=driver_version,
                    cuda_version=cuda_version,
                    compute_capability=(props.major, props.minor)
                )
                
                self.gpus.append(gpu_info)
                print(f"      GPU {i}: {name} ({total_memory}MB)")
                
            except Exception as e:
                print(f"      ⚠️ Error detecting GPU {i}: {e}")
        
        # Select primary GPU (first one for now)
        if self.gpus:
            self.primary_gpu = self.gpus[0]
    
    def _select_profile(self) -> None:
        """Select optimal GPU profile based on detected hardware"""
        if not self.primary_gpu:
            self.profile = GPU_PROFILES['default']
            return
        
        gpu_name = self.primary_gpu.name
        
        # Try exact match first
        for profile_name, profile in GPU_PROFILES.items():
            if profile_name.lower() in gpu_name.lower():
                self.profile = profile
                return
        
        # Match by VRAM size if no exact match
        vram_mb = self.primary_gpu.total_memory_mb
        
        if vram_mb >= 24000:  # 24GB+
            self.profile = GPU_PROFILES.get('NVIDIA GeForce RTX 4090', GPU_PROFILES['default'])
        elif vram_mb >= 16000:  # 16GB+
            self.profile = GPU_PROFILES.get('Tesla T4', GPU_PROFILES['default'])
        elif vram_mb >= 12000:  # 12GB+
            self.profile = GPU_PROFILES.get('NVIDIA GeForce RTX 3060', GPU_PROFILES['default'])
        else:
            self.profile = GPU_PROFILES['default']
    
    def get_optimal_config(self) -> Dict:
        """
        Get optimal configuration for the detected GPU.
        Returns a dict that can be used to override Config values.
        """
        if not self.profile:
            return {}
        
        return {
            # Whisper (transcription)
            'FASTER_WHISPER_MODEL': self.profile.whisper_model,
            'FASTER_WHISPER_DEVICE': 'cuda' if self.primary_gpu else 'cpu',
            'FASTER_WHISPER_COMPUTE_TYPE': self.profile.whisper_compute_type,
            'FASTER_WHISPER_BEAM_SIZE': self.profile.whisper_beam_size,
            
            # Video export
            'MAX_PARALLEL_EXPORTS': self.profile.max_parallel_exports,
            'VIDEO_BITRATE': self.profile.video_bitrate,
            'NVENC_PRESET': self.profile.nvenc_preset,
            'VIDEO_CODEC': 'h264_nvenc' if self.primary_gpu else 'libx264',
            'USE_GPU_ACCELERATION': bool(self.primary_gpu),
            
            # Processing
            'PROCESSING_CONCURRENCY': self.profile.optimal_workers,
            'MAX_BATCH_SIZE': self.profile.max_batch_size,
        }
    
    def apply_to_config(self, config_class) -> None:
        """Apply optimal settings to the Config class"""
        optimal = self.get_optimal_config()
        
        for key, value in optimal.items():
            if hasattr(config_class, key):
                setattr(config_class, key, value)
                print(f"   ⚙️  {key} = {value}")
    
    def get_gpu_stats(self) -> Dict:
        """Get current GPU statistics"""
        if not self.primary_gpu:
            return {'available': False, 'message': 'No GPU detected'}
        
        stats = {
            'available': True,
            'count': len(self.gpus),
            'gpus': []
        }
        
        for gpu in self.gpus:
            # Refresh GPU info
            gpu_stats = {
                'index': gpu.index,
                'name': gpu.name,
                'total_memory_mb': gpu.total_memory_mb,
                'free_memory_mb': gpu.free_memory_mb,
                'used_memory_mb': gpu.used_memory_mb,
                'memory_utilization': gpu.memory_utilization,
                'temperature': gpu.temperature,
                'utilization': gpu.utilization,
                'driver_version': gpu.driver_version,
                'cuda_version': gpu.cuda_version,
            }
            
            # Update from NVML if available
            if NVML_AVAILABLE:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(gpu.index)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_stats['free_memory_mb'] = mem_info.free // (1024 * 1024)
                    gpu_stats['used_memory_mb'] = mem_info.used // (1024 * 1024)
                    gpu_stats['temperature'] = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_stats['utilization'] = util.gpu
                    gpu_stats['memory_utilization'] = (gpu_stats['used_memory_mb'] / gpu_stats['total_memory_mb']) * 100
                except:
                    pass
            
            stats['gpus'].append(gpu_stats)
        
        # Add profile info
        if self.profile:
            stats['profile'] = {
                'name': self.profile.name,
                'description': self.profile.description,
                'whisper_model': self.profile.whisper_model,
                'max_parallel_exports': self.profile.max_parallel_exports,
            }
        
        return stats
    
    def start_monitoring(self, interval_seconds: float = 1.0, history_size: int = 60) -> None:
        """Start background GPU monitoring thread"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._gpu_stats_history = []
        
        def monitor_loop():
            while self._monitoring:
                stats = self.get_gpu_stats()
                stats['timestamp'] = time.time()
                
                self._gpu_stats_history.append(stats)
                
                # Keep only last N entries
                if len(self._gpu_stats_history) > history_size:
                    self._gpu_stats_history = self._gpu_stats_history[-history_size:]
                
                time.sleep(interval_seconds)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("   📊 GPU monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background GPU monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        print("   📊 GPU monitoring stopped")
    
    def get_monitoring_history(self) -> List[Dict]:
        """Get GPU stats history"""
        return self._gpu_stats_history.copy()
    
    def optimize_cuda_memory(self) -> None:
        """
        Optimize CUDA memory allocation settings.
        Configures PyTorch memory allocator for optimal performance.
        """
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return
        
        # Enable memory-efficient attention if available (PyTorch 2.0+)
        if hasattr(torch.backends, 'cuda'):
            # Enable TF32 for faster computation on Ampere+ GPUs
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
        
        # Enable cuDNN benchmark for consistent input sizes
        torch.backends.cudnn.benchmark = True
        
        # Set memory fraction to leave some headroom for NVENC
        if self.primary_gpu:
            # Leave ~2GB for NVENC and system
            reserved_mb = 2048
            available_mb = self.primary_gpu.total_memory_mb - reserved_mb
            fraction = min(0.9, available_mb / self.primary_gpu.total_memory_mb)
            torch.cuda.set_per_process_memory_fraction(fraction)
        
        print("   🎯 CUDA memory optimized")
    
    def clear_gpu_memory(self) -> None:
        """Clear GPU memory cache"""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return
        
        import gc
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        print("   🧹 GPU memory cleared")
    
    def estimate_processing_time(self, video_duration_seconds: float) -> Dict:
        """
        Estimate processing time based on GPU capabilities.
        Returns breakdown of transcription, analysis, and export times.
        """
        if not self.profile:
            # CPU fallback estimates
            return {
                'transcription_minutes': video_duration_seconds / 60 * 10,  # 10x realtime
                'analysis_minutes': video_duration_seconds / 60 * 2,
                'export_minutes': video_duration_seconds / 60 * 5,
                'total_minutes': video_duration_seconds / 60 * 17,
                'device': 'cpu'
            }
        
        # GPU estimates based on profile
        # T4 can do ~30x realtime with large-v3
        transcription_speed = 30 if 'T4' in self.profile.name else 20
        analysis_speed = 50  # Much faster with GPU
        export_speed = 60 * self.profile.max_parallel_exports  # Parallel exports
        
        transcription_min = video_duration_seconds / 60 / transcription_speed
        analysis_min = video_duration_seconds / 60 / analysis_speed
        export_min = video_duration_seconds / 60 / export_speed * 10  # Assume 10 clips
        
        return {
            'transcription_minutes': round(transcription_min, 1),
            'analysis_minutes': round(analysis_min, 1),
            'export_minutes': round(export_min, 1),
            'total_minutes': round(transcription_min + analysis_min + export_min, 1),
            'device': 'gpu',
            'gpu_name': self.profile.name
        }


# Global optimizer instance
_gpu_optimizer: Optional[GPUOptimizer] = None


def get_gpu_optimizer() -> GPUOptimizer:
    """Get or create the global GPU optimizer instance"""
    global _gpu_optimizer
    if _gpu_optimizer is None:
        _gpu_optimizer = GPUOptimizer()
    return _gpu_optimizer


def auto_configure_for_gpu(config_class) -> Dict:
    """
    Auto-configure the application for optimal GPU performance.
    Call this at startup to apply optimal settings.
    
    Returns the applied configuration.
    """
    optimizer = get_gpu_optimizer()
    
    print("\n🚀 AUTO-CONFIGURING FOR GPU PERFORMANCE...")
    optimizer.apply_to_config(config_class)
    optimizer.optimize_cuda_memory()
    
    return optimizer.get_optimal_config()


def get_aws_instance_type() -> Optional[str]:
    """Detect AWS EC2 instance type from metadata"""
    try:
        import urllib.request
        # AWS Instance Metadata Service v1
        url = "http://169.254.169.254/latest/meta-data/instance-type"
        req = urllib.request.Request(url, headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'})
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.read().decode('utf-8')
    except:
        return None


def is_aws_environment() -> bool:
    """Check if running on AWS EC2"""
    return get_aws_instance_type() is not None


# AWS-specific optimizations
AWS_INSTANCE_PROFILES = {
    'g4dn.xlarge': {
        'gpu': 'Tesla T4',
        'vcpu': 4,
        'memory_gb': 16,
        'recommended_workers': 4,
        'recommended_parallel_exports': 4,
    },
    'g4dn.2xlarge': {
        'gpu': 'Tesla T4',
        'vcpu': 8,
        'memory_gb': 32,
        'recommended_workers': 6,
        'recommended_parallel_exports': 6,
    },
    'g4dn.4xlarge': {
        'gpu': 'Tesla T4',
        'vcpu': 16,
        'memory_gb': 64,
        'recommended_workers': 8,
        'recommended_parallel_exports': 8,
    },
    'g5.xlarge': {
        'gpu': 'NVIDIA A10G',
        'vcpu': 4,
        'memory_gb': 16,
        'recommended_workers': 4,
        'recommended_parallel_exports': 6,
    },
    'g5.2xlarge': {
        'gpu': 'NVIDIA A10G',
        'vcpu': 8,
        'memory_gb': 32,
        'recommended_workers': 6,
        'recommended_parallel_exports': 8,
    },
}


def get_aws_recommendations() -> Dict:
    """Get AWS-specific recommendations based on instance type"""
    instance_type = get_aws_instance_type()
    
    if not instance_type:
        return {'is_aws': False}
    
    profile = AWS_INSTANCE_PROFILES.get(instance_type, {})
    
    return {
        'is_aws': True,
        'instance_type': instance_type,
        **profile
    }
