import { useState, useEffect } from 'react'
import axios from 'axios'

function ProcessingStatus({ filename, settings, onComplete, onError }) {
  const [status, setStatus] = useState({
    status: 'processing',
    progress: 0,
    message: 'Memulai analisis...'
  })

  useEffect(() => {
    startProcessing()
  }, [])

  const startProcessing = async () => {
    try {
      // Start processing
      const response = await axios.post('/api/process', {
        filename: filename,
        language: settings.language,
        target_duration: settings.targetDuration,
        style: settings.style,
        use_timoty_hooks: settings.useTimotyHook,
        auto_caption: settings.autoCaption
      })

      if (response.data.success) {
        onComplete(response.data)
      }
    } catch (error) {
      console.error('Processing error:', error)
      setStatus({
        status: 'error',
        progress: 0,
        message: error.response?.data?.error || 'Terjadi kesalahan saat memproses video'
      })
      onError()
    }
  }

  const getProgressColor = () => {
    if (status.progress < 30) return 'from-red-500 to-orange-500'
    if (status.progress < 70) return 'from-orange-500 to-yellow-500'
    return 'from-yellow-500 to-green-500'
  }

  return (
    <div className="card">
      <div className="text-center space-y-6">
        {/* Icon */}
        <div className="relative inline-block">
          <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center animate-pulse-slow">
            <span className="text-5xl">🎬</span>
          </div>
          <div className="absolute -bottom-2 -right-2 w-12 h-12 bg-gradient-to-br from-accent-500 to-primary-500 rounded-full flex items-center justify-center animate-bounce-slow">
            <span className="text-2xl">✨</span>
          </div>
        </div>

        {/* Status */}
        <div>
          <h2 className="text-3xl font-bold mb-2">
            {status.status === 'error' ? 'Terjadi Kesalahan' : 'Sedang Memproses Video'}
          </h2>
          <p className="text-white/70 text-lg">
            {status.message}
          </p>
        </div>

        {/* Progress Bar */}
        {status.status !== 'error' && (
          <div className="space-y-2">
            <div className="w-full h-4 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${getProgressColor()} transition-all duration-500 rounded-full`}
                style={{ width: `${status.progress}%` }}
              >
                <div className="w-full h-full shimmer"></div>
              </div>
            </div>
            <p className="text-sm text-white/60">
              {status.progress}% selesai
            </p>
          </div>
        )}

        {/* Processing Steps */}
        {status.status !== 'error' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            {[
              { step: 1, label: 'Analisis Video', icon: '🎥', progress: 0 },
              { step: 2, label: 'Analisis Audio', icon: '🎤', progress: 40 },
              { step: 3, label: 'Generate Klip', icon: '✂️', progress: 70 }
            ].map((item) => (
              <div
                key={item.step}
                className={`
                  card-hover p-4
                  ${status.progress >= item.progress ? 'border-2 border-primary-500' : ''}
                `}
              >
                <div className="text-3xl mb-2">{item.icon}</div>
                <div className="text-sm font-medium">{item.label}</div>
                {status.progress >= item.progress && (
                  <div className="mt-2 text-xs text-primary-400">
                    ✓ {status.progress === item.progress ? 'Sedang proses...' : 'Selesai'}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Error Message */}
        {status.status === 'error' && (
          <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p className="text-red-300">{status.message}</p>
          </div>
        )}

        {/* Info */}
        <div className="text-sm text-white/50 space-y-1">
          <p>⏱️ Proses ini bisa memakan waktu 2-10 menit</p>
          <p>💡 Jangan tutup halaman ini sampai proses selesai</p>
        </div>
      </div>
    </div>
  )
}

export default ProcessingStatus
