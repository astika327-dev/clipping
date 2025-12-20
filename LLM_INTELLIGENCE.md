# 🧠 LLM Intelligence - AI-Powered Clip Analysis

## Overview

**LLM Intelligence** adalah modul AI yang menggunakan **Groq LLama API** untuk memproses video menjadi clip secara lebih pintar. Modul ini menganalisis setiap clip yang dihasilkan dan menambahkan insight berbasis AI untuk meningkatkan kualitas output.

---

## ✨ Fitur Utama

### 1. **Context Validation** 🎯

Memvalidasi apakah clip memiliki konteks yang lengkap dan jelas:

- Apakah clip dimulai dengan jelas (tidak terpotong di tengah kalimat)
- Apakah clip memiliki pesan/point yang jelas
- Apakah clip berakhir dengan baik (tidak menggantung)
- Apakah clip bisa dipahami tanpa konteks sebelumnya

**Output:**

```json
{
  "context_complete": true,
  "context_score": 85,
  "context_issues": []
}
```

### 2. **Viral Title Generation** 🔥

Menghasilkan judul viral yang menarik untuk setiap clip:

- 5 variasi judul otomatis
- Terinspirasi dari Timothy Ronald, MrBeast, Alex Hormozi
- Optimized untuk TikTok, Reels, dan YouTube Shorts

**Output:**

```json
{
  "ai_title": "3 Kesalahan Fatal yang Bikin Kamu Gagal Closing!",
  "title_alternatives": [
    "Ini Rahasia Closing yang Gak Pernah Diomongin",
    "STOP! Jangan Lakukan Ini Kalau Mau Sukses",
    "Fakta Pahit: Kenapa 90% Orang Gagal di Bisnis"
  ]
}
```

### 3. **Hook Enhancement** 💡

Meningkatkan kualitas hook pembuka clip:

- Analisis hook original
- Generate 3 alternatif hook yang lebih kuat
- Rekomendasi hook terbaik

**Output:**

```json
{
  "enhanced_hooks": [
    "Tau gak? Ini kesalahan yang bikin 90% orang gagal",
    "INI PENTING: Rahasia closing yang jarang dibahas"
  ],
  "recommended_hook": "Tau gak? Ini kesalahan yang bikin 90% orang gagal"
}
```

### 4. **Content Analysis** 📊

Analisis mendalam tentang konten clip:

- Summary dalam 2-3 kalimat
- Key points utama
- Tipe konten (educational, emotional, controversial, entertaining, motivational)
- Target audience

**Output:**

```json
{
  "summary": "Speaker menjelaskan 3 kesalahan fatal dalam closing sales...",
  "key_points": [
    "Jangan terlalu cepat pitch",
    "Dengarkan dulu pain point",
    "Build trust first"
  ],
  "content_type": "educational"
}
```

### 5. **Quality Assessment** ⭐

Penilaian kualitas clip menggunakan AI:

- Hook strength (0-100)
- Content value (0-100)
- Engagement potential (0-100)
- Completeness (0-100)
- Watchability (0-100)

**Output:**

```json
{
  "quality_score": 78,
  "quality_level": "good",
  "quality_feedback": "Hook bisa lebih kuat; Ending sangat impactful"
}
```

### 6. **Trend Matching** 📈

Mencocokkan konten dengan trending topics:

- Matching dengan 20+ trending topics Indonesia
- Trend score
- Virality potential prediction

**Output:**

```json
{
  "matching_trends": ["self improvement", "mindset sukses", "bisnis online"],
  "trend_score": 75
}
```

### 7. **Social Media Captions** 📱

Generate caption siap pakai untuk berbagai platform:

- TikTok caption (dengan emoji dan CTA)
- Instagram Reels caption
- YouTube Shorts title
- Recommended hashtags

**Output:**

```json
{
  "social_captions": {
    "tiktok": "🔥 Ini kesalahan fatal yang bikin 90% orang gagal! #fyp #viral",
    "instagram": "3 kesalahan fatal dalam closing sales...\n\n💡 Setuju gak?\n\n#sales #closing #tips",
    "youtube_shorts": "3 Kesalahan Fatal dalam Closing Sales",
    "hashtags": ["fyp", "viral", "sales", "bisnis", "tips"]
  }
}
```

---

## 🚀 Setup

### 1. Dapatkan Groq API Key (GRATIS!)

Groq menyediakan free tier dengan **14,400 requests/day**.

1. Buka https://console.groq.com/keys
2. Buat akun atau login dengan Google
3. Generate API key baru
4. Copy API key

### 2. Konfigurasi Environment

Edit file `backend/.env`:

```env
# Groq API Key (sama untuk Whisper dan LLM)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx

# LLM Intelligence Settings
LLM_INTELLIGENCE_ENABLED=true
LLM_MODEL=llama-3.3-70b-versatile
```

### 3. Model Options

| Model                     | Kecepatan     | Kualitas        | Context Window |
| ------------------------- | ------------- | --------------- | -------------- |
| `llama-3.3-70b-versatile` | 🟢 Fast       | ⭐⭐⭐⭐⭐ Best | 128K           |
| `llama-3.1-8b-instant`    | 🟢 Very Fast  | ⭐⭐⭐⭐ Good   | 131K           |
| `llama-3.2-3b-preview`    | 🟢 Ultra Fast | ⭐⭐⭐ Basic    | 8K             |
| `mixtral-8x7b-32768`      | 🟢 Fast       | ⭐⭐⭐⭐ Good   | 32K            |

**Recommendation:** Gunakan `llama-3.3-70b-versatile` untuk kualitas terbaik.

---

## 📊 Contoh Output Clip dengan LLM Intelligence

```json
{
  "id": 1,
  "filename": "clip_001.mp4",
  "title": "Kesalahan Fatal dalam Closing",
  "ai_title": "3 Kesalahan Fatal yang Bikin Kamu Gagal Closing!",
  "title_alternatives": [
    "STOP! Ini yang Bikin Prospek Kabur",
    "Fakta Pahit: Kenapa 90% Salesman Gagal"
  ],
  "viral_score": "Tinggi",
  "viral_score_numeric": 0.82,
  "ai_quality_boost": 15,

  "ai_intelligence": {
    "context_complete": true,
    "context_score": 92,
    "context_issues": [],

    "summary": "Speaker membahas 3 kesalahan umum yang membuat sales gagal melakukan closing, dengan fokus pada pentingnya mendengarkan pain point customer terlebih dahulu.",
    "key_points": [
      "Jangan langsung pitch produk",
      "Dengarkan pain point customer",
      "Build rapport dan trust dulu"
    ],
    "content_type": "educational",

    "quality_score": 85,
    "quality_level": "excellent",
    "quality_feedback": "Hook sangat kuat, konten valuable, ending impactful",

    "matching_trends": ["sales tips", "bisnis online", "self improvement"],
    "trend_score": 80,

    "enhanced_hooks": [
      "Tau gak kenapa prospek kamu kabur?",
      "INI kesalahan yang bikin 90% sales gagal closing"
    ],
    "recommended_hook": "Tau gak kenapa prospek kamu kabur?"
  },

  "social_captions": {
    "tiktok": "🔥 Ini kesalahan yang bikin prospek kabur! Save biar gak lupa #fyp #sales #tips",
    "instagram": "3 Kesalahan Fatal dalam Closing Sales 📈\n\nJangan sampai kamu melakukan ini...\n\n#sales #bisnis #tips #closing #marketing",
    "youtube_shorts": "3 Kesalahan Fatal yang Bikin Gagal Closing",
    "hashtags": [
      "fyp",
      "viral",
      "sales",
      "bisnis",
      "tips",
      "closing",
      "marketing",
      "entrepreneur"
    ]
  }
}
```

---

## 🔧 Fallback Mode

Jika tidak ada API key atau koneksi gagal, LLM Intelligence tetap berjalan dalam **fallback mode**:

- Menggunakan algoritma keyword-based sederhana
- Tetap generate title dan caption basic
- Quality assessment berdasarkan heuristics

Ini memastikan software tetap berfungsi meskipun tanpa API key.

---

## 💡 Tips Penggunaan

1. **Untuk Podcast/Monolog**: LLM Intelligence sangat efektif karena bisa memahami konteks percakapan panjang dan memilih momen-momen terbaik.

2. **Untuk Konten Educational**: Gunakan model `llama-3.3-70b-versatile` untuk analisis yang lebih mendalam.

3. **Untuk Batch Processing**: Perhatikan rate limit Groq (14,400 request/day). Untuk video panjang dengan banyak clips, pertimbangkan menggunakan model yang lebih cepat.

4. **Caption Ready-to-Use**: Social media captions bisa langsung di-copy paste ke TikTok/Instagram saat posting.

---

## 🔄 Future Improvements

- [ ] **Keyword Extraction**: Auto-extract keywords untuk SEO
- [ ] **Thumbnail Suggestion**: AI recommend thumbnail style
- [ ] **Music Matching**: Suggest trending music berdasarkan konten
- [ ] **Competitor Analysis**: Bandingkan dengan viral clips serupa
- [ ] **A/B Testing Suggestions**: Multiple hook variants untuk testing

---

## 📝 Changelog

### v1.0.0 (December 2024)

- ✅ Initial release
- ✅ Context Validation
- ✅ Viral Title Generation (5 variants)
- ✅ Hook Enhancement (3 alternatives)
- ✅ Content Analysis & Summarization
- ✅ Quality Assessment (5 dimensions)
- ✅ Trend Matching (20+ topics)
- ✅ Social Media Captions (TikTok, IG, YouTube)
- ✅ Fallback mode untuk offline usage

---

**Made with ❤️ for Indonesian Content Creators**
