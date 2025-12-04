import { useState, useRef } from 'react'
import axios from 'axios'

function VideoUploader({ onVideoUploaded }) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
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

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-6">Upload Video</h2>
      
      <div
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center
          transition-all duration-300
          ${isDragging 
            ? 'border-primary-400 bg-primary-500/10' 
            : 'border-white/30 hover:border-white/50'
          }
          ${uploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/mov,video/avi,video/mkv"
          onChange={handleFileSelect}
          className="hidden"
        />

        {uploading ? (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-lg font-medium">Uploading video...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-6xl">📹</div>
            <div>
              <p className="text-xl font-semibold mb-2">
                Drag & drop video atau klik untuk pilih file
              </p>
              <p className="text-white/60 text-sm">
                Format: MP4, MOV, AVI, MKV • Max: 2GB • Durasi: 60 menit
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
          <p className="text-red-300 text-sm">❌ {error}</p>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="card-hover text-center">
          <div className="text-3xl mb-2">🎯</div>
          <h3 className="font-semibold mb-1">Analisis Otomatis</h3>
          <p className="text-white/60 text-xs">
            AI menganalisis audio & visual untuk temukan momen terbaik
          </p>
        </div>
        <div className="card-hover text-center">
          <div className="text-3xl mb-2">✂️</div>
          <h3 className="font-semibold mb-1">Potong Otomatis</h3>
          <p className="text-white/60 text-xs">
            Generate klip 9-32 detik dengan hook kuat & ending nendang
          </p>
        </div>
        <div className="card-hover text-center">
          <div className="text-3xl mb-2">🚀</div>
          <h3 className="font-semibold mb-1">Skor Viral</h3>
          <p className="text-white/60 text-xs">
            Setiap klip diberi skor potensi viral berdasarkan konten
          </p>
        </div>
      </div>
    </div>
  )
}

export default VideoUploader
