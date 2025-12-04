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
from datetime import datetime
import traceback

from config import Config
from video_analyzer import VideoAnalyzer
from audio_analyzer import AudioAnalyzer
from clip_generator import ClipGenerator
import psutil

app = Flask(__name__)
CORS(app)

# Load configuration
app.config.from_object(Config)

# Store processing status
processing_status = {}
processing_semaphore = threading.Semaphore(Config.PROCESSING_CONCURRENCY)
JOB_ID_PATTERN = re.compile(r'^[A-Za-z0-9_\-]+$')

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
            
            audio_analyzer = AudioAnalyzer(filepath, Config)
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
            
            # Step 4: Export Clips
            processing_status[job_id]['message'] = 'Exporting clips...'
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
                        'language': audio_analysis['transcript']['language'],
                        'overall': audio_analysis['analysis']['overall']
                    },
                    'options': {
                        'language': language,
                        'target_duration': target_duration,
                        'style': style,
                        'use_timoty_hooks': use_timoty_hooks,
                        'auto_caption': auto_caption
                    }
                }, f, indent=2, ensure_ascii=False)
            
            # Update status
            processing_status[job_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Processing complete!',
                'clips': clips,
                'job_id': job_id,
                'output_dir': output_dir
            }
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'clips': clips
            })
        
        except Exception as e:
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
            'timestamp': datetime.utcnow().isoformat() + 'Z',
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
