"""
LLM Intelligence Module
AI-Powered Clip Intelligence using Groq LLama API

Features:
1. Smart Context Validation - Validates if clip is contextually complete
2. Viral Title Generation - Generates engaging titles for each clip
3. Content Summarization - Summarizes clip content for better understanding
4. Hook Enhancement - AI improves/generates better hooks
5. Quality Scoring - AI-powered quality assessment
6. Trend Matching - Matches content with trending topics
7. Caption Generation - Creates engaging captions for social media

Author: AI Video Clipper
Version: 1.0.0
"""

import os
import re
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# Try to import httpx for API calls
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️ httpx not installed. LLM Intelligence features will be limited.")


class ContentQuality(Enum):
    """Content quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


@dataclass
class ClipIntelligence:
    """Intelligence data for a single clip"""
    # Context validation
    is_context_complete: bool = True
    context_score: float = 1.0
    context_issues: List[str] = field(default_factory=list)
    
    # Title generation
    viral_titles: List[str] = field(default_factory=list)
    recommended_title: str = ""
    
    # Content analysis
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    content_type: str = "general"  # educational, emotional, controversial, entertaining
    
    # Hook enhancement
    original_hook: str = ""
    enhanced_hooks: List[str] = field(default_factory=list)
    recommended_hook: str = ""
    
    # Quality assessment
    quality_score: float = 0.0
    quality_level: str = "average"
    quality_feedback: str = ""
    
    # Trend matching
    matching_trends: List[str] = field(default_factory=list)
    trend_score: float = 0.0
    
    # Social media captions
    tiktok_caption: str = ""
    instagram_caption: str = ""
    youtube_shorts_title: str = ""
    
    # Hashtags
    recommended_hashtags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.available = False
    
    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        raise NotImplementedError


class GroqLLM(LLMProvider):
    """Groq LLM Provider - Fast and Free!"""
    
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    # Available models (as of 2024)
    MODELS = {
        'llama-3.3-70b-versatile': {'context': 128000, 'speed': 'fast'},
        'llama-3.1-8b-instant': {'context': 131072, 'speed': 'very_fast'},
        'llama-3.2-3b-preview': {'context': 8192, 'speed': 'ultra_fast'},
        'mixtral-8x7b-32768': {'context': 32768, 'speed': 'fast'},
        'gemma2-9b-it': {'context': 8192, 'speed': 'fast'},
    }
    
    def __init__(self, api_key: str = None, model: str = 'llama-3.3-70b-versatile'):
        super().__init__(api_key or os.environ.get('GROQ_API_KEY', ''))
        self.model = model
        self.available = bool(self.api_key) and HTTPX_AVAILABLE
        
        if self.available:
            print(f"   ✅ Groq LLM initialized with model: {model}")
        else:
            if not self.api_key:
                print("   ⚠️ Groq LLM: No API key provided")
            if not HTTPX_AVAILABLE:
                print("   ⚠️ Groq LLM: httpx not installed")
    
    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        """Generate response using Groq API"""
        if not self.available:
            return ""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    print(f"   ⚠️ Groq API error: {response.status_code} - {response.text}")
                    return ""
                    
        except Exception as e:
            print(f"   ⚠️ Groq API exception: {e}")
            return ""


class LLMIntelligence:
    """
    Main LLM Intelligence Engine
    Provides AI-powered analysis and enhancement for video clips
    """
    
    # System prompts for different tasks
    SYSTEM_PROMPTS = {
        'context_validator': """Kamu adalah AI yang ahli dalam menilai apakah sebuah klip video podcast/konten memiliki konteks yang lengkap dan jelas.
Tugas kamu adalah menganalisis transkrip klip dan menentukan:
1. Apakah klip dimulai dengan jelas (tidak terpotong di tengah kalimat)
2. Apakah klip memiliki pesan/point yang jelas
3. Apakah klip berakhir dengan baik (tidak menggantung)
4. Apakah klip bisa dipahami tanpa konteks sebelumnya

Berikan penilaian dalam format JSON yang valid.""",

        'title_generator': """Kamu adalah kreator konten viral yang ahli membuat judul menarik untuk TikTok, Reels, dan YouTube Shorts.
Gaya kamu terinspirasi dari kreator sukses seperti:
- Timothy Ronald (hook kuat, mental slap)
- MrBeast (curiosity gap, angka spesifik)
- Alex Hormozi (value-first, direct)

Buat judul yang:
- Memancing rasa penasaran
- Menggunakan angka jika relevan
- Memiliki hook emosional
- Singkat dan punchy (max 60 karakter)

Berikan 5 variasi judul dalam format JSON.""",

        'hook_enhancer': """Kamu adalah scriptwriter viral yang ahli membuat hook pembuka yang kuat.
Hook yang baik harus:
- Menarik perhatian dalam 3 detik pertama
- Membuat penonton ingin terus menonton
- Bisa berupa pertanyaan, fakta mengejutkan, atau statement kontroversial
- Relevan dengan konten

Berikan 3 variasi hook yang lebih baik dari original dalam format JSON.""",

        'content_analyzer': """Kamu adalah analis konten yang ahli memahami dan meringkas konten video.
Tugas kamu:
1. Ringkas konten dalam 2-3 kalimat
2. Identifikasi key points utama
3. Tentukan kategori konten (educational, emotional, controversial, entertaining, motivational)
4. Identifikasi target audiens

Berikan analisis dalam format JSON.""",

        'quality_assessor': """Kamu adalah quality assessor untuk konten short-form video.
Nilai klip berdasarkan:
1. Hook strength (0-100): Seberapa kuat pembukaan
2. Content value (0-100): Seberapa bernilai kontennya
3. Engagement potential (0-100): Potensi engagement
4. Completeness (0-100): Kelengkapan pesan
5. Watchability (0-100): Seberapa enak ditonton

Berikan penilaian dan feedback dalam format JSON.""",

        'caption_generator': """Kamu adalah social media manager yang ahli membuat caption viral.
Buat caption untuk:
1. TikTok: Singkat, pakai emoji, CTA jelas
2. Instagram Reels: Medium length, hashtag-friendly
3. YouTube Shorts: Hook-focused, searchable

Include recommended hashtags (mix populer dan niche).
Berikan dalam format JSON.""",

        'trend_matcher': """Kamu adalah trend analyst yang memahami trending topics di social media Indonesia.
Analisis konten ini dan cocokkan dengan:
1. Trending topics saat ini
2. Evergreen topics yang selalu relevan
3. Niche-specific trends

Berikan matching trends dan skor relevansi dalam format JSON."""
    }
    
    # Trending topics database (can be updated dynamically)
    TRENDING_TOPICS_ID = [
        'self improvement', 'produktivitas', 'mindset sukses', 'finansial',
        'relationship', 'kesehatan mental', 'karir', 'bisnis online',
        'content creator', 'AI dan teknologi', 'investasi', 'crypto',
        'passive income', 'personal branding', 'public speaking',
        'storytelling', 'leadership', 'time management', 'networking',
        'work life balance', 'burnout', 'quarter life crisis', 'gen z life'
    ]
    
    def __init__(self, config=None):
        """Initialize LLM Intelligence with configuration"""
        self.config = config
        
        # Get API key from config or environment
        api_key = None
        if config and hasattr(config, 'GROQ_API_KEY'):
            api_key = config.GROQ_API_KEY
        if not api_key:
            api_key = os.environ.get('GROQ_API_KEY', '')
        
        # Get LLM model preference
        llm_model = os.environ.get('LLM_MODEL', 'llama-3.3-70b-versatile')
        
        # Initialize Groq LLM
        self.llm = GroqLLM(api_key=api_key, model=llm_model)
        self.available = self.llm.available
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Cache for repeated analyses
        self._cache = {}
        
        if self.available:
            print("   ✅ LLM Intelligence initialized successfully")
        else:
            print("   ⚠️ LLM Intelligence running in fallback mode (no API key)")
    
    def _rate_limit(self):
        """Simple rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response, handling markdown code blocks"""
        if not response:
            return {}
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            response = json_match.group(1)
        
        # Try to find JSON object in response
        try:
            # First try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON-like structure
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                try:
                    return json.loads(response[json_start:json_end])
                except json.JSONDecodeError:
                    pass
        
        return {}
    
    def _fallback_context_validation(self, text: str) -> Dict:
        """Fallback context validation without LLM"""
        issues = []
        score = 1.0
        
        # Check for sentence start
        first_words = ['jadi', 'terus', 'nah', 'ya', 'dan', 'tapi', 'karena', 'makanya']
        text_lower = text.lower().strip()
        for word in first_words:
            if text_lower.startswith(word + ' '):
                issues.append(f"Klip dimulai dengan kata sambung '{word}'")
                score -= 0.15
                break
        
        # Check for proper ending
        if not text.strip().endswith(('.', '!', '?', '"', "'")):
            issues.append("Klip tidak berakhir dengan tanda baca yang jelas")
            score -= 0.1
        
        # Check text length (at least 50 characters for meaningful content)
        if len(text) < 50:
            issues.append("Konten terlalu pendek untuk konteks yang jelas")
            score -= 0.2
        
        return {
            'is_complete': score >= 0.7,
            'score': max(0, score),
            'issues': issues
        }
    
    def validate_context(self, transcript: str, clip_start: float = 0, clip_end: float = 0) -> Dict:
        """
        Validate if a clip has complete context
        
        Args:
            transcript: The clip's transcript text
            clip_start: Start time of clip
            clip_end: End time of clip
            
        Returns:
            Dict with validation results
        """
        if not transcript or len(transcript.strip()) < 10:
            return {
                'is_complete': False,
                'score': 0.0,
                'issues': ['Transkrip kosong atau terlalu pendek']
            }
        
        # Use fallback if LLM not available
        if not self.available:
            return self._fallback_context_validation(transcript)
        
        self._rate_limit()
        
        prompt = f"""Analisis transkrip klip video berikut:

TRANSKRIP:
"{transcript}"

DURASI: {clip_end - clip_start:.1f} detik

Berikan penilaian dalam format JSON:
{{
    "is_complete": true/false,
    "score": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "start_quality": "baik/kurang/buruk",
    "end_quality": "baik/kurang/buruk",
    "message_clarity": "jelas/kurang jelas/tidak jelas"
}}"""
        
        response = self.llm.generate(prompt, self.SYSTEM_PROMPTS['context_validator'], temperature=0.3)
        result = self._parse_json_response(response)
        
        if not result:
            return self._fallback_context_validation(transcript)
        
        return {
            'is_complete': result.get('is_complete', True),
            'score': float(result.get('score', 0.8)),
            'issues': result.get('issues', []),
            'start_quality': result.get('start_quality', 'baik'),
            'end_quality': result.get('end_quality', 'baik'),
            'message_clarity': result.get('message_clarity', 'jelas')
        }
    
    def generate_viral_titles(self, transcript: str, content_type: str = 'general') -> List[str]:
        """
        Generate viral title options for a clip
        
        Args:
            transcript: The clip's transcript text
            content_type: Type of content (educational, emotional, etc.)
            
        Returns:
            List of title suggestions
        """
        if not self.available or not transcript:
            return self._fallback_title_generation(transcript)
        
        self._rate_limit()
        
        prompt = f"""Buatkan 5 judul viral untuk klip dengan transkrip berikut:

TRANSKRIP:
"{transcript[:500]}"

TIPE KONTEN: {content_type}

Berikan dalam format JSON:
{{
    "titles": [
        "Judul 1",
        "Judul 2",
        "Judul 3",
        "Judul 4",
        "Judul 5"
    ],
    "recommended": "Judul terbaik",
    "reasoning": "Alasan memilih judul ini"
}}"""
        
        response = self.llm.generate(prompt, self.SYSTEM_PROMPTS['title_generator'], temperature=0.8)
        result = self._parse_json_response(response)
        
        if result and 'titles' in result:
            return result.get('titles', [])
        
        return self._fallback_title_generation(transcript)
    
    def _fallback_title_generation(self, transcript: str) -> List[str]:
        """Fallback title generation without LLM"""
        if not transcript:
            return ["Untitled Clip"]
        
        # Extract first meaningful sentence
        sentences = re.split(r'[.!?]', transcript)
        first_sentence = sentences[0].strip() if sentences else transcript[:50]
        
        # Clean and truncate
        title = first_sentence[:60]
        if len(first_sentence) > 60:
            title = title.rsplit(' ', 1)[0] + '...'
        
        return [
            title,
            f"🔥 {title}",
            f"WAJIB TAU: {title[:40]}...",
        ]
    
    def enhance_hook(self, original_hook: str, transcript: str) -> Dict:
        """
        Enhance or generate better hook for a clip
        
        Args:
            original_hook: The current hook text
            transcript: Full transcript for context
            
        Returns:
            Dict with enhanced hook options
        """
        if not self.available:
            return self._fallback_hook_enhancement(original_hook, transcript)
        
        self._rate_limit()
        
        prompt = f"""Hook original: "{original_hook}"

Konteks konten:
"{transcript[:400]}"

Buatkan 3 hook alternatif yang lebih kuat.

Format JSON:
{{
    "hooks": [
        "Hook 1 (lebih menarik)",
        "Hook 2 (lebih kontroversial)",
        "Hook 3 (lebih emosional)"
    ],
    "recommended": "Hook terbaik",
    "hook_type": "question/statement/fact/controversial"
}}"""
        
        response = self.llm.generate(prompt, self.SYSTEM_PROMPTS['hook_enhancer'], temperature=0.8)
        result = self._parse_json_response(response)
        
        if result and 'hooks' in result:
            return {
                'original': original_hook,
                'enhanced_hooks': result.get('hooks', []),
                'recommended': result.get('recommended', original_hook),
                'hook_type': result.get('hook_type', 'statement')
            }
        
        return self._fallback_hook_enhancement(original_hook, transcript)
    
    def _fallback_hook_enhancement(self, original_hook: str, transcript: str) -> Dict:
        """Fallback hook enhancement without LLM"""
        hooks = []
        
        # Add question version
        if not original_hook.endswith('?'):
            hooks.append(f"Tau gak? {original_hook}")
        
        # Add emphasis version
        hooks.append(f"INI PENTING: {original_hook}")
        
        # Add curiosity gap version
        hooks.append(f"Rahasia yang jarang dibahas: {original_hook[:30]}...")
        
        return {
            'original': original_hook,
            'enhanced_hooks': hooks,
            'recommended': hooks[0] if hooks else original_hook,
            'hook_type': 'statement'
        }
    
    def analyze_content(self, transcript: str) -> Dict:
        """
        Analyze and summarize clip content
        
        Args:
            transcript: The clip's transcript text
            
        Returns:
            Dict with content analysis
        """
        if not self.available:
            return self._fallback_content_analysis(transcript)
        
        self._rate_limit()
        
        prompt = f"""Analisis konten video berikut:

TRANSKRIP:
"{transcript}"

Format JSON:
{{
    "summary": "Ringkasan 2-3 kalimat",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "content_type": "educational/emotional/controversial/entertaining/motivational",
    "target_audience": "Deskripsi target audiens",
    "main_message": "Pesan utama",
    "tone": "serius/santai/inspiratif/provokatif"
}}"""
        
        response = self.llm.generate(prompt, self.SYSTEM_PROMPTS['content_analyzer'], temperature=0.5)
        result = self._parse_json_response(response)
        
        if result:
            return {
                'summary': result.get('summary', ''),
                'key_points': result.get('key_points', []),
                'content_type': result.get('content_type', 'general'),
                'target_audience': result.get('target_audience', 'General audience'),
                'main_message': result.get('main_message', ''),
                'tone': result.get('tone', 'neutral')
            }
        
        return self._fallback_content_analysis(transcript)
    
    def _fallback_content_analysis(self, transcript: str) -> Dict:
        """Fallback content analysis without LLM"""
        # Simple keyword-based content type detection
        text_lower = transcript.lower()
        
        content_type = 'general'
        if any(word in text_lower for word in ['cara', 'tips', 'tutorial', 'belajar', 'langkah']):
            content_type = 'educational'
        elif any(word in text_lower for word in ['sedih', 'bahagia', 'marah', 'kecewa', 'bangga']):
            content_type = 'emotional'
        elif any(word in text_lower for word in ['kontroversial', 'debat', 'salah', 'bohong']):
            content_type = 'controversial'
        elif any(word in text_lower for word in ['lucu', 'ngakak', 'kocak', 'gokil']):
            content_type = 'entertaining'
        elif any(word in text_lower for word in ['semangat', 'sukses', 'berhasil', 'jangan menyerah']):
            content_type = 'motivational'
        
        # Simple summary (first 2 sentences)
        sentences = re.split(r'[.!?]', transcript)
        summary = '. '.join(sentences[:2]).strip() + '.' if sentences else transcript[:100]
        
        return {
            'summary': summary,
            'key_points': [],
            'content_type': content_type,
            'target_audience': 'General audience',
            'main_message': sentences[0].strip() if sentences else '',
            'tone': 'neutral'
        }
    
    def assess_quality(self, transcript: str, duration: float, has_faces: bool = True) -> Dict:
        """
        Assess clip quality using AI
        
        Args:
            transcript: The clip's transcript text
            duration: Clip duration in seconds
            has_faces: Whether clip has face visible
            
        Returns:
            Dict with quality assessment
        """
        if not self.available:
            return self._fallback_quality_assessment(transcript, duration, has_faces)
        
        self._rate_limit()
        
        prompt = f"""Nilai kualitas klip video berikut:

TRANSKRIP:
"{transcript}"

DURASI: {duration:.1f} detik
ADA WAJAH: {"Ya" if has_faces else "Tidak"}

Format JSON:
{{
    "scores": {{
        "hook_strength": 0-100,
        "content_value": 0-100,
        "engagement_potential": 0-100,
        "completeness": 0-100,
        "watchability": 0-100
    }},
    "overall_score": 0-100,
    "quality_level": "excellent/good/average/poor",
    "strengths": ["Kelebihan 1", "Kelebihan 2"],
    "weaknesses": ["Kekurangan 1", "Kekurangan 2"],
    "improvement_suggestions": ["Saran 1", "Saran 2"]
}}"""
        
        response = self.llm.generate(prompt, self.SYSTEM_PROMPTS['quality_assessor'], temperature=0.4)
        result = self._parse_json_response(response)
        
        if result and 'scores' in result:
            return {
                'scores': result.get('scores', {}),
                'overall_score': result.get('overall_score', 50),
                'quality_level': result.get('quality_level', 'average'),
                'strengths': result.get('strengths', []),
                'weaknesses': result.get('weaknesses', []),
                'improvement_suggestions': result.get('improvement_suggestions', [])
            }
        
        return self._fallback_quality_assessment(transcript, duration, has_faces)
    
    def _fallback_quality_assessment(self, transcript: str, duration: float, has_faces: bool) -> Dict:
        """Fallback quality assessment without LLM"""
        scores = {
            'hook_strength': 50,
            'content_value': 50,
            'engagement_potential': 50,
            'completeness': 50,
            'watchability': 50
        }
        
        # Adjust based on simple heuristics
        text_length = len(transcript)
        
        # Content value based on length
        if text_length > 200:
            scores['content_value'] += 20
        elif text_length < 50:
            scores['content_value'] -= 20
        
        # Duration scoring
        if 15 <= duration <= 30:
            scores['watchability'] += 15
        elif duration < 10 or duration > 45:
            scores['watchability'] -= 15
        
        # Face presence
        if has_faces:
            scores['engagement_potential'] += 10
        
        overall = sum(scores.values()) / len(scores)
        
        quality_level = 'average'
        if overall >= 75:
            quality_level = 'excellent'
        elif overall >= 60:
            quality_level = 'good'
        elif overall < 40:
            quality_level = 'poor'
        
        return {
            'scores': scores,
            'overall_score': overall,
            'quality_level': quality_level,
            'strengths': ['Konten memiliki durasi yang baik' if 15 <= duration <= 30 else ''],
            'weaknesses': [],
            'improvement_suggestions': []
        }
    
    def generate_captions(self, transcript: str, content_type: str = 'general') -> Dict:
        """
        Generate social media captions for clip
        
        Args:
            transcript: The clip's transcript text
            content_type: Type of content
            
        Returns:
            Dict with platform-specific captions
        """
        if not self.available:
            return self._fallback_caption_generation(transcript, content_type)
        
        self._rate_limit()
        
        prompt = f"""Buat caption untuk berbagai platform sosial media:

TRANSKRIP:
"{transcript[:400]}"

TIPE KONTEN: {content_type}

Format JSON:
{{
    "tiktok": {{
        "caption": "Caption untuk TikTok (max 150 chars, emoji, CTA)",
        "sounds": ["Saran lagu trending 1", "Saran lagu 2"]
    }},
    "instagram": {{
        "caption": "Caption untuk Instagram Reels (medium length)",
        "hashtags_inline": ["hashtag1", "hashtag2"]
    }},
    "youtube_shorts": {{
        "title": "Judul untuk YouTube Shorts (max 100 chars)",
        "description": "Deskripsi singkat"
    }},
    "recommended_hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
    "best_posting_time": "Waktu posting terbaik"
}}"""
        
        response = self.llm.generate(prompt, self.SYSTEM_PROMPTS['caption_generator'], temperature=0.7)
        result = self._parse_json_response(response)
        
        if result:
            return {
                'tiktok': result.get('tiktok', {}),
                'instagram': result.get('instagram', {}),
                'youtube_shorts': result.get('youtube_shorts', {}),
                'recommended_hashtags': result.get('recommended_hashtags', []),
                'best_posting_time': result.get('best_posting_time', 'Prime time (19:00-21:00)')
            }
        
        return self._fallback_caption_generation(transcript, content_type)
    
    def _fallback_caption_generation(self, transcript: str, content_type: str) -> Dict:
        """Fallback caption generation without LLM"""
        # Extract first sentence for caption
        sentences = re.split(r'[.!?]', transcript)
        first_sentence = sentences[0].strip()[:100] if sentences else transcript[:100]
        
        # Simple hashtag generation based on content type
        base_hashtags = ['fyp', 'viral', 'indonesia']
        type_hashtags = {
            'educational': ['edukasi', 'belajar', 'tips', 'tutorial'],
            'emotional': ['curhat', 'lifestory', 'motivasi'],
            'controversial': ['opini', 'fakta', 'truth'],
            'entertaining': ['lucu', 'ngakak', 'comedy'],
            'motivational': ['semangat', 'inspirasi', 'sukses']
        }
        
        hashtags = base_hashtags + type_hashtags.get(content_type, ['konten'])
        
        return {
            'tiktok': {
                'caption': f"🔥 {first_sentence} #fyp #viral",
                'sounds': []
            },
            'instagram': {
                'caption': f"{first_sentence}\n\n💡 Setuju gak?\n\n#{' #'.join(hashtags[:5])}",
                'hashtags_inline': hashtags[:5]
            },
            'youtube_shorts': {
                'title': first_sentence[:80],
                'description': transcript[:150] + '...'
            },
            'recommended_hashtags': hashtags,
            'best_posting_time': 'Prime time (19:00-21:00)'
        }
    
    def match_trends(self, transcript: str) -> Dict:
        """
        Match content with trending topics
        
        Args:
            transcript: The clip's transcript text
            
        Returns:
            Dict with trend matching results
        """
        if not self.available:
            return self._fallback_trend_matching(transcript)
        
        self._rate_limit()
        
        trending_topics_str = ', '.join(self.TRENDING_TOPICS_ID)
        
        prompt = f"""Analisis konten ini dan cocokkan dengan trending topics:

TRANSKRIP:
"{transcript[:500]}"

TRENDING TOPICS SAAT INI:
{trending_topics_str}

Format JSON:
{{
    "matching_trends": ["Trend 1", "Trend 2"],
    "trend_score": 0.0-1.0,
    "trend_category": "trending/evergreen/niche",
    "virality_potential": "high/medium/low",
    "audience_size": "large/medium/small",
    "competition_level": "high/medium/low",
    "recommendation": "Rekomendasi strategi posting"
}}"""
        
        response = self.llm.generate(prompt, self.SYSTEM_PROMPTS['trend_matcher'], temperature=0.5)
        result = self._parse_json_response(response)
        
        if result:
            return {
                'matching_trends': result.get('matching_trends', []),
                'trend_score': float(result.get('trend_score', 0.5)),
                'trend_category': result.get('trend_category', 'evergreen'),
                'virality_potential': result.get('virality_potential', 'medium'),
                'audience_size': result.get('audience_size', 'medium'),
                'competition_level': result.get('competition_level', 'medium'),
                'recommendation': result.get('recommendation', '')
            }
        
        return self._fallback_trend_matching(transcript)
    
    def _fallback_trend_matching(self, transcript: str) -> Dict:
        """Fallback trend matching without LLM"""
        text_lower = transcript.lower()
        
        matching_trends = []
        for topic in self.TRENDING_TOPICS_ID:
            if topic.lower() in text_lower:
                matching_trends.append(topic)
        
        # Check for related keywords
        trend_keywords = {
            'self improvement': ['berkembang', 'improve', 'lebih baik', 'growth'],
            'produktivitas': ['produktif', 'efisien', 'waktu', 'fokus'],
            'mindset sukses': ['mindset', 'pola pikir', 'sukses', 'berhasil'],
            'finansial': ['uang', 'keuangan', 'investasi', 'nabung', 'cuan'],
        }
        
        for trend, keywords in trend_keywords.items():
            if trend not in matching_trends:
                if any(kw in text_lower for kw in keywords):
                    matching_trends.append(trend)
        
        trend_score = min(1.0, len(matching_trends) * 0.3)
        
        return {
            'matching_trends': matching_trends[:5],
            'trend_score': trend_score,
            'trend_category': 'evergreen' if matching_trends else 'niche',
            'virality_potential': 'medium',
            'audience_size': 'medium',
            'competition_level': 'medium',
            'recommendation': 'Post during prime time for maximum reach'
        }
    
    def analyze_clip_full(self, transcript: str, duration: float, 
                          has_faces: bool = True, original_hook: str = "") -> ClipIntelligence:
        """
        Perform full AI analysis on a clip
        
        Args:
            transcript: The clip's transcript text
            duration: Clip duration in seconds
            has_faces: Whether clip has face visible
            original_hook: The original hook line
            
        Returns:
            ClipIntelligence object with all analysis results
        """
        intelligence = ClipIntelligence()
        
        if not transcript:
            return intelligence
        
        # 1. Context Validation
        context_result = self.validate_context(transcript)
        intelligence.is_context_complete = context_result.get('is_complete', True)
        intelligence.context_score = context_result.get('score', 0.8)
        intelligence.context_issues = context_result.get('issues', [])
        
        # 2. Content Analysis
        content_result = self.analyze_content(transcript)
        intelligence.summary = content_result.get('summary', '')
        intelligence.key_points = content_result.get('key_points', [])
        intelligence.content_type = content_result.get('content_type', 'general')
        
        # 3. Title Generation
        intelligence.viral_titles = self.generate_viral_titles(transcript, intelligence.content_type)
        if intelligence.viral_titles:
            intelligence.recommended_title = intelligence.viral_titles[0]
        
        # 4. Hook Enhancement
        if original_hook:
            hook_result = self.enhance_hook(original_hook, transcript)
            intelligence.original_hook = original_hook
            intelligence.enhanced_hooks = hook_result.get('enhanced_hooks', [])
            intelligence.recommended_hook = hook_result.get('recommended', original_hook)
        
        # 5. Quality Assessment
        quality_result = self.assess_quality(transcript, duration, has_faces)
        intelligence.quality_score = quality_result.get('overall_score', 50)
        intelligence.quality_level = quality_result.get('quality_level', 'average')
        intelligence.quality_feedback = '; '.join(quality_result.get('improvement_suggestions', []))
        
        # 6. Trend Matching
        trend_result = self.match_trends(transcript)
        intelligence.matching_trends = trend_result.get('matching_trends', [])
        intelligence.trend_score = trend_result.get('trend_score', 0.5)
        
        # 7. Caption Generation
        caption_result = self.generate_captions(transcript, intelligence.content_type)
        if 'tiktok' in caption_result:
            intelligence.tiktok_caption = caption_result['tiktok'].get('caption', '')
        if 'instagram' in caption_result:
            intelligence.instagram_caption = caption_result['instagram'].get('caption', '')
        if 'youtube_shorts' in caption_result:
            intelligence.youtube_shorts_title = caption_result['youtube_shorts'].get('title', '')
        intelligence.recommended_hashtags = caption_result.get('recommended_hashtags', [])
        
        return intelligence
    
    def batch_analyze_clips(self, clips: List[Dict]) -> List[Dict]:
        """
        Analyze multiple clips and add intelligence data
        
        Args:
            clips: List of clip dictionaries with 'text', 'duration', etc.
            
        Returns:
            List of clips with added 'intelligence' field
        """
        print(f"\n🧠 Running LLM Intelligence on {len(clips)} clips...")
        
        for i, clip in enumerate(clips):
            print(f"   📊 Analyzing clip {i+1}/{len(clips)}...")
            
            transcript = clip.get('text', '')
            duration = clip.get('duration', 0)
            has_faces = clip.get('visual', {}).get('has_faces', True)
            original_hook = clip.get('hook_overlay', {}).get('text', '')
            
            # Full analysis
            intelligence = self.analyze_clip_full(
                transcript=transcript,
                duration=duration,
                has_faces=has_faces,
                original_hook=original_hook
            )
            
            # Add to clip
            clip['intelligence'] = intelligence.to_dict()
            
            # Update clip metadata with AI insights
            if intelligence.recommended_title:
                clip['ai_title'] = intelligence.recommended_title
            if intelligence.recommended_hook:
                clip['ai_hook'] = intelligence.recommended_hook
            if intelligence.tiktok_caption:
                clip['tiktok_caption'] = intelligence.tiktok_caption
            if intelligence.instagram_caption:
                clip['instagram_caption'] = intelligence.instagram_caption
            
            # Adjust viral score based on AI quality assessment
            if 'viral_score' in clip and intelligence.quality_score > 0:
                # Blend original score with AI score
                original_score = clip['viral_score']
                ai_score = intelligence.quality_score / 100  # Normalize to 0-1
                clip['viral_score'] = (original_score * 0.6) + (ai_score * 0.4)
                clip['ai_quality_score'] = intelligence.quality_score
        
        print(f"   ✅ LLM Intelligence analysis complete!")
        return clips


# Singleton instance for easy access
_llm_intelligence_instance = None

def get_llm_intelligence(config=None) -> LLMIntelligence:
    """Get or create LLM Intelligence singleton"""
    global _llm_intelligence_instance
    if _llm_intelligence_instance is None:
        _llm_intelligence_instance = LLMIntelligence(config)
    return _llm_intelligence_instance


# Test function
def test_llm_intelligence():
    """Test LLM Intelligence functionality"""
    print("\n🧪 Testing LLM Intelligence...")
    
    llm = LLMIntelligence()
    
    test_transcript = """
    Jadi gini guys, salah satu kesalahan fatal yang sering dilakukan anak muda adalah 
    mereka terlalu fokus ke gaji besar tapi lupa sama yang namanya skill building. 
    Padahal kalau lo punya skill yang langka dan valuable, uang itu akan dateng sendiri. 
    Trust me, gue udah buktiin sendiri. Waktu awal-awal gue kerja, gue rela digaji kecil 
    asal bisa belajar dari orang-orang terbaik di industri. Dan sekarang? Those skills 
    made me irreplaceable.
    """
    
    print("\n1️⃣ Testing Context Validation...")
    context = llm.validate_context(test_transcript)
    print(f"   Complete: {context.get('is_complete')}, Score: {context.get('score')}")
    
    print("\n2️⃣ Testing Title Generation...")
    titles = llm.generate_viral_titles(test_transcript, 'educational')
    print(f"   Titles: {titles[:2]}")
    
    print("\n3️⃣ Testing Content Analysis...")
    content = llm.analyze_content(test_transcript)
    print(f"   Type: {content.get('content_type')}, Summary: {content.get('summary', '')[:100]}...")
    
    print("\n4️⃣ Testing Full Analysis...")
    intelligence = llm.analyze_clip_full(test_transcript, duration=25.0)
    print(f"   Quality: {intelligence.quality_level} ({intelligence.quality_score})")
    print(f"   Trends: {intelligence.matching_trends[:3]}")
    
    print("\n✅ LLM Intelligence test complete!")
    return intelligence


if __name__ == "__main__":
    test_llm_intelligence()
