"""
Flask Backend for AI Video Clipper
Main application file
"""
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import shutil
import re
import threading
import time
from datetime import datetime, timedelta, timezone
import traceback

from config import Config
from video_analyzer import VideoAnalyzer
from audio_analyzer import AudioAnalyzer
from clip_generator import ClipGenerator
import psutil

try:
    import yt_dlp
    YTDLPDownloadError = yt_dlp.utils.DownloadError
except ImportError:  # pragma: no cover - optional dependency outside tests
    yt_dlp = None
    class YTDLPDownloadError(Exception):
        """Fallback exception when yt-dlp is unavailable."""
        pass

app = Flask(__name__)
CORS(app)

# Load configuration
app.config.from_object(Config)

# Store processing status
processing_status = {}
processing_semaphore = threading.Semaphore(Config.PROCESSING_CONCURRENCY)
JOB_ID_PATTERN = re.compile(r'^[A-Za-z0-9_\-]+$')
MODEL_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_\-\.]+$')
DEVICE_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_:\-]+$')
YOUTUBE_URL_PATTERN = re.compile(
    r'^(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/.+',
    re.IGNORECASE
)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def get_file_size(filepath):
    """Get file size in bytes"""
    return os.path.getsize(filepath)


def is_safe_job_id(job_id):
    """Validate job identifier to prevent path traversal."""
    return bool(job_id and JOB_ID_PATTERN.fullmatch(job_id))


def is_safe_filename(filename):
    """Ensure filenames remain sanitized across requests."""
    return bool(filename and secure_filename(filename) == filename)


def is_safe_model_name(name):
    """Limit whisper model inputs to alphanumeric-friendly tokens."""
    return bool(name and MODEL_NAME_PATTERN.fullmatch(name))


def is_safe_device_name(name):
    """Validate device or compute descriptors."""
    return bool(name and DEVICE_NAME_PATTERN.fullmatch(name))


def is_valid_youtube_url(url):
    """Basic validation to guard youtube downloader endpoint."""
    return bool(url and YOUTUBE_URL_PATTERN.match(url.strip()))


def collect_process_stats(keyword):
    """Collect memory and CPU usage for processes containing keyword."""
    stats = []
    keyword = keyword.lower()
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            name = (proc.info.get('name') or '').lower()
            if keyword not in name:
                continue
            mem_info = proc.info.get('memory_info')
            rss = getattr(mem_info, 'rss', 0) if mem_info else 0
            stats.append({
                'pid': proc.info['pid'],
                'name': proc.info.get('name'),
                'memory_bytes': rss,
                'memory_mb': round(rss / (1024 * 1024), 2),
                'cpu_percent': proc.cpu_percent(interval=0.0)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return stats

def get_video_duration(filepath):
    """Get video duration using FFmpeg"""
    import subprocess
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 0

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'AI Video Clipper API is running'
    })

@app.route('/api/upload', methods=['POST'])
def upload_video():
    """
    Upload video endpoint
    """
    try:
        # Check if file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Save file
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Check file size
        file_size = get_file_size(filepath)
        if file_size > Config.MAX_VIDEO_SIZE:
            os.remove(filepath)
            return jsonify({
                'error': f'File too large. Maximum size: {Config.MAX_VIDEO_SIZE / (1024**3):.1f}GB'
            }), 400
        
        # Check video duration
        duration = get_video_duration(filepath)
        if duration > Config.MAX_VIDEO_DURATION:
            os.remove(filepath)
            return jsonify({
                'error': f'Video too long. Maximum duration: {Config.MAX_VIDEO_DURATION / 60:.0f} minutes'
            }), 400
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'size': file_size,
            'duration': duration
        })
    
    except Exception as e:
        print(f"Error uploading video: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/youtube', methods=['POST'])
def download_youtube_video():
    """Download a YouTube video directly into the uploads folder."""
    if yt_dlp is None:
        return jsonify({'error': 'yt-dlp belum terpasang di server. Jalankan pip install yt-dlp'}), 500

    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()

    if not url:
        return jsonify({'error': 'URL YouTube wajib diisi'}), 400
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'URL harus berasal dari YouTube'}), 400

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ydl_opts = {
        'format': 'bv*+ba/best',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(Config.UPLOAD_FOLDER, '%(id)s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 2,
    }

    temp_path = None
    final_path = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError('Tidak bisa mengambil informasi video YouTube')

            temp_path = info.get('_filename') or ydl.prepare_filename(info)
            if not os.path.exists(temp_path):
                requested = info.get('requested_downloads') or []
                for item in requested:
                    candidate = item.get('filepath')
                    if candidate and os.path.exists(candidate):
                        temp_path = candidate
                        break

            if not (temp_path and os.path.exists(temp_path)):
                raise FileNotFoundError('File hasil unduhan tidak ditemukan')

            raw_extension = os.path.splitext(temp_path)[1] or '.mp4'
            safe_title = secure_filename(info.get('title') or '')
            if not safe_title:
                safe_title = info.get('id', 'youtube_video')
            final_filename = f"{timestamp}_{safe_title}_{info.get('id', 'yt')}{raw_extension}"
            final_path = os.path.join(Config.UPLOAD_FOLDER, final_filename)
            shutil.move(temp_path, final_path)

            file_size = get_file_size(final_path)
            if file_size > Config.MAX_VIDEO_SIZE:
                os.remove(final_path)
                return jsonify({'error': 'File terlalu besar setelah diunduh (maks 2GB)'}), 400

            duration = info.get('duration') or get_video_duration(final_path)
            if duration > Config.MAX_VIDEO_DURATION:
                os.remove(final_path)
                return jsonify({'error': 'Durasi video YouTube melebihi batas 60 menit'}), 400

            return jsonify({
                'success': True,
                'filename': final_filename,
                'filepath': final_path,
                'size': file_size,
                'duration': duration,
                'source': 'youtube',
                'title': info.get('title'),
                'channel': info.get('uploader'),
                'url': url
            })

    except YTDLPDownloadError as e:
        if final_path and os.path.exists(final_path):
            try:
                os.remove(final_path)
            except OSError:
                pass
        error_message = getattr(e, 'exc_info', [None, None, None])[1]
        readable = str(error_message or e)
        return jsonify({'error': f'Gagal mengunduh video: {readable}'}), 400
    except Exception as e:
        if final_path and os.path.exists(final_path):
            try:
                os.remove(final_path)
            except OSError:
                pass
        print(f"Error downloading YouTube video: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        # Hapus file sementara bila masih tersisa
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

import numpy as np

def convert_numpy_types(obj):
    """
    Convert numpy types to native python types for JSON serialization
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'item'):
        return obj.item()
    return obj

@app.route('/api/process', methods=['POST'])
def process_video():
    """
    Process video and generate clips
    """
    if not processing_semaphore.acquire(blocking=False):
        return jsonify({
            'error': 'Server sedang memproses video lain. Silakan coba lagi sebentar lagi.'
        }), 429

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 400
        
        # Get parameters
        filename = data.get('filename')
        language = data.get('language', 'id')
        target_duration = data.get('target_duration', 'all')
        style = data.get('style', 'balanced')
        use_timoty_hooks = bool(data.get('use_timoty_hooks', False))
        auto_caption = bool(data.get('auto_caption', False))

        backend_choice = str(data.get('transcription_backend', '') or '').strip().lower()
        overrides = {}
        if backend_choice in {'faster-whisper', 'openai-whisper'}:
            overrides['transcription_backend'] = backend_choice

        override_fields = [
            ('whisper_model', 'whisper_model', is_safe_model_name),
            ('faster_whisper_model', 'faster_whisper_model', is_safe_model_name),
            ('faster_whisper_compute_type', 'faster_whisper_compute_type', is_safe_model_name),
            ('faster_whisper_device', 'faster_whisper_device', is_safe_device_name)
        ]

        for payload_key, override_key, validator in override_fields:
            value = data.get(payload_key)
            if isinstance(value, str):
                trimmed = value.strip()
                if validator(trimmed):
                    overrides[override_key] = trimmed
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Video file not found'}), 404
        
        # Create job ID
        job_id = filename.replace('.', '_')
        
        # Initialize status
        processing_status[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Starting analysis...',
            'clips': []
        }
        
        # Process in background (for production, use Celery or similar)
        # For now, we'll process synchronously
        
        try:
            # Step 1: Video Analysis
            processing_status[job_id]['message'] = 'Analyzing video...'
            processing_status[job_id]['progress'] = 10
            
            video_analyzer = VideoAnalyzer(filepath, Config)
            video_analysis = video_analyzer.analyze()
            
            # Step 2: Audio Analysis
            processing_status[job_id]['message'] = 'Analyzing audio...'
            processing_status[job_id]['progress'] = 40
            
            audio_analyzer = AudioAnalyzer(filepath, Config, overrides=overrides)
            audio_analysis = audio_analyzer.analyze(language)
            
            # Step 3: Generate Clips
            processing_status[job_id]['message'] = 'Generating clips...'
            processing_status[job_id]['progress'] = 70
            
            clip_generator = ClipGenerator(filepath, Config)
            clips = clip_generator.generate_clips(
                video_analysis,
                audio_analysis,
                target_duration,
                style,
                hook_mode='timoty' if use_timoty_hooks else None
            )
            if auto_caption:
                clip_generator.attach_captions(
                    clips,
                    audio_analysis['transcript'].get('segments', [])
                )
            
            # CRITICAL CHECK: Ensure we have clips
            if not clips:
                print("🚨 CRITICAL: No clips generated! This should never happen.")
                print("   Attempting emergency clip creation...")
                # Last resort: create clips from video duration
                video_duration = video_analysis.get('duration') or video_analysis.get('metadata', {}).get('duration', 60)
                clips = [
                    {
                        'id': 1,
                        'filename': 'clip_001.mp4',
                        'title': 'Clip 1',
                        'start_time': '0:00:00',
                        'end_time': str(timedelta(seconds=min(20, video_duration))),
                        'start_seconds': 0,
                        'end_seconds': min(20, video_duration),
                        'duration': min(20, video_duration),
                        'viral_score': 'Rendah',
                        'viral_score_numeric': 0.2,
                        'reason': 'Emergency fallback',
                        'category': 'educational',
                        'transcript': 'Auto-generated clip'
                    }
                ]
            
            # Step 4: Export Clips
            processing_status[job_id]['message'] = f'Exporting {len(clips)} clips...'
            processing_status[job_id]['progress'] = 85
            
            # Create output directory for this job
            output_dir = os.path.join(Config.OUTPUT_FOLDER, job_id)
            os.makedirs(output_dir, exist_ok=True)
            
            # Export clips
            exported_files = clip_generator.export_all_clips(clips, output_dir)
            
            # Convert clips to native types
            clips = convert_numpy_types(clips)
            video_analysis = convert_numpy_types(video_analysis)
            audio_analysis = convert_numpy_types(audio_analysis)
            
            # Save metadata
            metadata_path = os.path.join(output_dir, 'metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'clips': clips,
                    'video_analysis': video_analysis,
                    'audio_analysis': {
                        'language': audio_analysis.get('transcript', {}).get('language', 'unknown'),
                        'overall': audio_analysis.get('analysis', {}).get('overall', {})
                    },
                    'options': {
                        'language': language,
                        'target_duration': target_duration,
                        'style': style,
                        'use_timoty_hooks': use_timoty_hooks,
                        'auto_caption': auto_caption
                    },
                    'stats': {
                        'total_clips': len(clips),
                        'exported_clips': len(exported_files)
                    }
                }, f, indent=2, ensure_ascii=False)
            
            # Update status
            processing_status[job_id] = {
                'status': 'completed',
                'progress': 100,
                'message': f'Processing complete! Generated {len(clips)} clips.',
                'clips': clips,
                'job_id': job_id,
                'output_dir': output_dir
            }
            
            print(f"✅ Job {job_id} completed with {len(clips)} clips")
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'clips': clips,
                'total_clips': len(clips)
            })
        
        except Exception as e:
            print(f"❌ Error in job {job_id}: {e}")
            traceback.print_exc()
            processing_status[job_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Error: {str(e)}',
                'clips': []
            }
            raise
    
    except Exception as e:
        print(f"Error processing video: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        # Give the CPU a short breather before accepting the next heavy job
        time.sleep(max(Config.PROCESSING_COOLDOWN_SECONDS, 0))
        processing_semaphore.release()

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """
    Get processing status
    """
    if not is_safe_job_id(job_id):
        return jsonify({'error': 'Invalid job ID'}), 400
    if job_id not in processing_status:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(convert_numpy_types(processing_status[job_id]))

@app.route('/api/download/<job_id>/<filename>', methods=['GET'])
def download_clip(job_id, filename):
    """
    Download a specific clip
    """
    try:
        if not (is_safe_job_id(job_id) and is_safe_filename(filename)):
            return jsonify({'error': 'Invalid parameters'}), 400
        output_dir = os.path.join(Config.OUTPUT_FOLDER, job_id)
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_from_directory(output_dir, filename, as_attachment=True)
    
    except Exception as e:
        print(f"Error downloading clip: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-all/<job_id>', methods=['GET'])
def download_all_clips(job_id):
    """
    Download all clips as a ZIP file
    """
    try:
        if not is_safe_job_id(job_id):
            return jsonify({'error': 'Invalid job ID'}), 400
        output_dir = os.path.join(Config.OUTPUT_FOLDER, job_id)
        
        if not os.path.exists(output_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Create ZIP file
        zip_path = os.path.join(Config.OUTPUT_FOLDER, f"{job_id}_clips.zip")
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', output_dir)
        
        return send_file(zip_path, as_attachment=True)
    
    except Exception as e:
        print(f"Error creating ZIP: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clips', methods=['GET'])
def get_all_clips():
    """
    Get all exported clips across all jobs
    Returns: List of clips with metadata
    """
    try:
        clips = []
        output_dir = config.OUTPUT_FOLDER
        
        if not os.path.exists(output_dir):
            return jsonify({'clips': []})
        
        # Iterate through all job folders
        for job_folder in os.listdir(output_dir):
            job_path = os.path.join(output_dir, job_folder)
            
            if not os.path.isdir(job_path):
                continue
            
            # Look for clip files
            for filename in os.listdir(job_path):
                if filename.endswith('.mp4') and filename.startswith('clip_'):
                    clip_path = os.path.join(job_path, filename)
                    
                    try:
                        # Get file info
                        file_size = os.path.getsize(clip_path)
                        mod_time = os.path.getmtime(clip_path)
                        
                        # Try to get video duration using ffprobe
                        duration = 0
                        try:
                            probe_cmd = [
                                'ffprobe', '-v', 'error',
                                '-show_entries', 'format=duration',
                                '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1',
                                clip_path
                            ]
                            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=5)
                            if result.stdout:
                                duration = float(result.stdout.strip())
                        except:
                            duration = 0
                        
                        # Get metadata if available
                        metadata = {}
                        metadata_file = os.path.join(job_path, 'metadata.json')
                        if os.path.exists(metadata_file):
                            try:
                                with open(metadata_file, 'r') as f:
                                    metadata = json.load(f)
                            except:
                                metadata = {}
                        
                        clips.append({
                            'id': f"{job_folder}-{filename}",
                            'jobId': job_folder,
                            'filename': filename,
                            'size': file_size,
                            'duration': duration,
                            'exportedAt': datetime.fromtimestamp(mod_time).isoformat(),
                            'metadata': metadata
                        })
                    except Exception as e:
                        print(f"Error processing clip {filename}: {e}")
                        continue
        
        # Sort by exported date (newest first)
        clips.sort(key=lambda x: x['exportedAt'], reverse=True)
        
        return jsonify({'clips': clips})
    
    except Exception as e:
        print(f"Error getting clips: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<job_id>/<filename>', methods=['DELETE'])
def delete_clip(job_id, filename):
    """
    Delete a single clip file
    """
    try:
        if not (is_safe_job_id(job_id) and is_safe_filename(filename)):
            return jsonify({'error': 'Invalid parameters'}), 400
        
        # Only allow clip deletion
        if not filename.startswith('clip_') or not filename.endswith('.mp4'):
            return jsonify({'error': 'Invalid clip file'}), 400
        
        clip_path = os.path.join(config.OUTPUT_FOLDER, job_id, filename)
        
        if not os.path.exists(clip_path):
            return jsonify({'error': 'Clip not found'}), 404
        
        os.remove(clip_path)
        print(f"✅ Deleted clip: {clip_path}")
        
        return jsonify({'message': 'Clip deleted successfully'})
    
    except Exception as e:
        print(f"Error deleting clip: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<job_id>/<filename>', methods=['GET'])
def preview_clip(job_id, filename):
    """
    Stream a clip for preview
    """
    try:
        if not (is_safe_job_id(job_id) and is_safe_filename(filename)):
            return jsonify({'error': 'Invalid parameters'}), 400
        output_dir = os.path.join(Config.OUTPUT_FOLDER, job_id)
        return send_from_directory(output_dir, filename)
    
    except Exception as e:
        print(f"Error previewing clip: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup/<job_id>', methods=['DELETE'])
def cleanup_job(job_id):
    """
    Clean up job files
    """
    try:
        if not is_safe_job_id(job_id):
            return jsonify({'error': 'Invalid job ID'}), 400
        # Remove output directory
        output_dir = os.path.join(Config.OUTPUT_FOLDER, job_id)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
        # Remove from status
        if job_id in processing_status:
            del processing_status[job_id]
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error cleaning up: {e}")
        return jsonify({'error': str(e)}), 500


def get_folder_size(path):
    """Calculate total folder size in bytes"""
    total = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total += os.path.getsize(filepath)
    return total


@app.route('/api/storage', methods=['GET'])
def storage_info():
    """Get storage usage for uploads and outputs"""
    try:
        uploads_size = get_folder_size(Config.UPLOAD_FOLDER)
        outputs_size = get_folder_size(Config.OUTPUT_FOLDER)
        
        # List files in uploads
        uploads_files = []
        if os.path.exists(Config.UPLOAD_FOLDER):
            for filename in os.listdir(Config.UPLOAD_FOLDER):
                if filename == '.gitkeep':
                    continue
                filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                if os.path.isfile(filepath):
                    uploads_files.append({
                        'filename': filename,
                        'size': os.path.getsize(filepath),
                        'size_mb': round(os.path.getsize(filepath) / (1024 * 1024), 2)
                    })
        
        return jsonify({
            'uploads': {
                'total_bytes': uploads_size,
                'total_mb': round(uploads_size / (1024 * 1024), 2),
                'total_gb': round(uploads_size / (1024 * 1024 * 1024), 2),
                'files': uploads_files
            },
            'outputs': {
                'total_bytes': outputs_size,
                'total_mb': round(outputs_size / (1024 * 1024), 2),
                'total_gb': round(outputs_size / (1024 * 1024 * 1024), 2)
            }
        })
    except Exception as e:
        print(f"Error getting storage info: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload/<filename>', methods=['DELETE'])
def delete_upload(filename):
    """Delete an uploaded video file"""
    try:
        # Validate filename
        if not is_safe_filename(filename):
            return jsonify({'error': 'Invalid filename'}), 400
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Ensure file is inside upload folder
        if not os.path.abspath(filepath).startswith(os.path.abspath(Config.UPLOAD_FOLDER)):
            return jsonify({'error': 'Invalid file path'}), 400
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Delete file
        os.remove(filepath)
        
        return jsonify({'success': True, 'message': f'Deleted {filename}'})
    
    except Exception as e:
        print(f"Error deleting file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload/delete-all', methods=['POST'])
def delete_all_uploads():
    """Delete ALL uploaded videos (use with caution!)"""
    try:
        deleted = []
        if os.path.exists(Config.UPLOAD_FOLDER):
            for filename in os.listdir(Config.UPLOAD_FOLDER):
                if filename == '.gitkeep':
                    continue
                filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                if os.path.isfile(filepath):
                    try:
                        os.remove(filepath)
                        deleted.append(filename)
                    except Exception as e:
                        print(f"Failed to delete {filename}: {e}")
        
        return jsonify({
            'success': True,
            'deleted_count': len(deleted),
            'deleted_files': deleted
        })
    
    except Exception as e:
        print(f"Error deleting uploads: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/system-stats', methods=['GET'])
def system_stats():
    """Expose lightweight system metrics for UI display."""
    try:
        virtual_mem = psutil.virtual_memory()
        total_mem = virtual_mem.total
        used_mem = virtual_mem.used
        available_mem = virtual_mem.available
        memory_percent = virtual_mem.percent
        cpu_percent = psutil.cpu_percent(interval=0.1)

        python_stats = collect_process_stats('python')
        node_stats = collect_process_stats('node')

        return jsonify({
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', '') + 'Z',
            'cpu_percent': cpu_percent,
            'memory': {
                'total_bytes': total_mem,
                'used_bytes': used_mem,
                'available_bytes': available_mem,
                'percent': memory_percent
            },
            'python_processes': python_stats,
            'node_processes': node_stats
        })
    except Exception as e:
        print(f"Error gathering system stats: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Serve frontend in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve frontend files"""
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
    
    if os.path.exists(frontend_dir):
        if path and os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        else:
            return send_from_directory(frontend_dir, 'index.html')
    else:
        return jsonify({
            'message': 'Frontend not built. Run: cd frontend && npm run build'
        })

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--production', action='store_true', help='Run in production mode')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    args = parser.parse_args()
    
    if args.production:
        print("🚀 Running in PRODUCTION mode")
        app.run(host='0.0.0.0', port=args.port, debug=False)
    else:
        print("🔧 Running in DEVELOPMENT mode")
        app.run(host='127.0.0.1', port=args.port, debug=True)
