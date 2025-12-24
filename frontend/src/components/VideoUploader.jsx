import { useState, useRef } from 'react'
import axios from 'axios'

function VideoUploader({ onVideoUploaded }) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [downloading, setDownloading] = useState(false)
  const [youtubeQuality, setYoutubeQuality] = useState('1080p')
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileUpload = async (file) => {
    setError(null)
    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('video', file)

      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          console.log(`Upload progress: ${percentCompleted}%`)
        }
      })

      if (response.data.success) {
        onVideoUploaded(response.data)
      }
    } catch (err) {
      console.error('Upload error:', err)
      setError(err.response?.data?.error || 'Gagal upload video. Silakan coba lagi.')
    } finally {
      setUploading(false)
    }
  }

  const handleYoutubeDownload = async () => {
    const trimmedUrl = youtubeUrl.trim()
    if (!trimmedUrl) {
      setError('Masukkan URL YouTube terlebih dahulu.')
      return
    }

    setError(null)
    setDownloading(true)
    try {
      const response = await axios.post('/api/youtube', { url: trimmedUrl, quality: youtubeQuality })
      if (response.data.success) {
        onVideoUploaded(response.data)
        setYoutubeUrl('')
      } else {
        setError(response.data.error || 'Gagal mengambil video dari YouTube.')
      }
    } catch (err) {
      console.error('YouTube download error:', err)
      setError(err.response?.data?.error || 'Gagal mengambil video dari YouTube. Coba ulangi atau gunakan link berbeda.')
    } finally {
      setDownloading(false)
    }
  }

  const handleYoutubeSubmit = (event) => {
    event.preventDefault()
    if (!downloading) {
      handleYoutubeDownload()
    }
  }

  return (
    <div className="card animate-slide-up">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-2xl">
          📤
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white">Upload Video</h2>
          <p className="text-white/50 text-sm">Drag & drop atau pilih file video</p>
        </div>
      </div>
      
      <div
        className={`
          relative rounded-2xl p-12 text-center
          transition-all duration-500 ease-out
          border-2 border-dashed
          ${isDragging 
            ? 'border-primary-400 bg-primary-500/10 scale-[1.02]' 
            : 'border-white/10 hover:border-primary-500/50 hover:bg-white/[0.02]'
          }
          ${(uploading || downloading) ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        {/* Glow effect on drag */}
        {isDragging && (
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-primary-500/20 to-accent-500/20 blur-xl" />
        )}
        
        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/mov,video/avi,video/mkv"
          onChange={handleFileSelect}
          className="hidden"
        />

        {uploading ? (
          <div className="space-y-6 relative">
            <div className="relative w-20 h-20 mx-auto">
              <div className="absolute inset-0 border-4 border-primary-500/20 rounded-full" />
              <div className="absolute inset-0 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
              <div className="absolute inset-2 border-4 border-accent-500 border-b-transparent rounded-full animate-spin" style={{ animationDirection: 'reverse' }} />
            </div>
            <div>
              <p className="text-xl font-semibold text-white">Uploading video...</p>
              <p className="text-white/50 text-sm mt-1">Mohon tunggu sebentar</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6 relative">
            <div className="w-24 h-24 mx-auto rounded-2xl bg-gradient-to-br from-primary-500/10 to-accent-500/10 border border-white/10 flex items-center justify-center animate-float">
              <span className="text-5xl">🎬</span>
            </div>
            <div>
              <p className="text-xl font-semibold text-white mb-2">
                Drag & drop video di sini
              </p>
              <p className="text-white/40 text-sm">
                atau <span className="text-primary-400 hover:text-primary-300 transition-colors">klik untuk browse</span>
              </p>
            </div>
            <div className="flex items-center justify-center gap-4 text-xs text-white/30">
              <span className="px-3 py-1 rounded-full bg-white/5">MP4</span>
              <span className="px-3 py-1 rounded-full bg-white/5">MOV</span>
              <span className="px-3 py-1 rounded-full bg-white/5">AVI</span>
              <span className="px-3 py-1 rounded-full bg-white/5">MKV</span>
            </div>
            <p className="text-white/30 text-xs">
              Maksimal 2GB • Durasi hingga 60 menit
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
          <p className="text-red-300 text-sm">❌ {error}</p>
        </div>
      )}

      <form onSubmit={handleYoutubeSubmit} className="mt-6 space-y-3">
        <label className="block text-sm font-semibold">
          Atau import langsung dari YouTube
        </label>
        <div className="flex flex-col lg:flex-row gap-3">
          <input
            type="url"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="input-field flex-1"
            disabled={downloading || uploading}
          />
          <select
            value={youtubeQuality}
            onChange={(e) => setYoutubeQuality(e.target.value)}
            className="input-field lg:w-32"
            disabled={downloading || uploading}
          >
            <option value="1080p">1080p</option>
            <option value="720p">720p</option>
            <option value="360p">360p</option>
          </select>
          <button
            type="submit"
            disabled={downloading || uploading}
            className="btn-primary md:w-48 flex items-center justify-center"
          >
            {downloading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Mengunduh...
              </span>
            ) : (
              <>
                <span className="mr-2">📥</span>
                Ambil dari YouTube
              </>
            )}
          </button>
        </div>
        <p className="text-white/50 text-xs">
          Link YouTube akan diunduh di server GPU, maksimal 60 menit dan 2GB. Pastikan video tidak private.
        </p>
      </form>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="feature-card group">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500/20 to-primary-600/10 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
            🎯
          </div>
          <h3 className="font-semibold text-white mb-2">Analisis Otomatis</h3>
          <p className="text-white/50 text-sm leading-relaxed">
            AI menganalisis audio & visual untuk temukan momen terbaik
          </p>
        </div>
        <div className="feature-card group">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-accent-500/20 to-accent-600/10 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
            ✂️
          </div>
          <h3 className="font-semibold text-white mb-2">Potong Otomatis</h3>
          <p className="text-white/50 text-sm leading-relaxed">
            Generate klip 9-32 detik dengan hook kuat & ending nendang
          </p>
        </div>
        <div className="feature-card group">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
            🚀
          </div>
          <h3 className="font-semibold text-white mb-2">Skor Viral</h3>
          <p className="text-white/50 text-sm leading-relaxed">
            Setiap klip diberi skor potensi viral berdasarkan konten
          </p>
        </div>
      </div>
    </div>
  )
}

export default VideoUploader
