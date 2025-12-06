import { useState, useEffect, useRef, useMemo } from 'react'
import axios from 'axios'

const STATUS_POLL_INTERVAL = 3000

function ProcessingStatus({ filename, jobId, settings, onComplete, onCancel }) {
  const [status, setStatus] = useState({
    status: 'queued',
    progress: 5,
    message: 'Menyiapkan GPU & memori...',
    clips: []
  })
  const [eventLog, setEventLog] = useState([])
  const [hasStarted, setHasStarted] = useState(false)
  const pollRef = useRef(null)

  const progressPercent = useMemo(() => {
    const value = Number(status.progress) || 0
    return Math.min(Math.max(Math.round(value), 0), 100)
  }, [status.progress])

  useEffect(() => {
    if (!filename || !jobId || hasStarted) return

    setHasStarted(true)
    launchProcessing()
    fetchStatus()
    pollRef.current = setInterval(fetchStatus, STATUS_POLL_INTERVAL)

    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [filename, jobId, hasStarted])

  const launchProcessing = () => {
    axios
      .post('/api/process', {
        filename,
        language: settings.language,
        target_duration: settings.targetDuration,
        style: settings.style,
        use_timoty_hooks: settings.useTimotyHook,
        auto_caption: settings.autoCaption
      })
      .catch((error) => {
        console.error('Processing error:', error)
        handleError(error.response?.data?.error || 'Terjadi kesalahan saat mengeksekusi proses.')
      })
  }

  const fetchStatus = async () => {
    try {
      const { data } = await axios.get(`/api/status/${jobId}`)
      setStatus((prev) => ({ ...prev, ...data }))

      if (data.message) {
        setEventLog((prev) => {
          if (prev.length && prev[prev.length - 1].message === data.message) return prev
          const next = [...prev, { message: data.message, timestamp: new Date().toISOString() }]
          return next.slice(-10)
        })
      }

      if (data.status === 'completed') {
        stopPolling()
        onComplete?.(data)
      } else if (data.status === 'error') {
        handleError(data.message || 'Proses gagal. Silakan coba lagi.')
      }
    } catch (error) {
      console.error('Status polling error:', error)
    }
  }

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const handleError = (message) => {
    stopPolling()
    setStatus({ status: 'error', progress: 0, message, clips: [] })
  }

  const progressSteps = [
    { key: 'video', label: 'Analisis Video', icon: '🎥', threshold: 10 },
    { key: 'audio', label: 'Analisis Audio', icon: '🎧', threshold: 40 },
    { key: 'clips', label: 'Generate Klip', icon: '✂️', threshold: 70 },
    { key: 'export', label: 'Export & Finalisasi', icon: '📦', threshold: 95 }
  ]

  const getProgressColor = () => {
    if (status.status === 'error') return 'from-red-500 to-red-700'
    if (progressPercent < 30) return 'from-orange-500 to-yellow-500'
    if (progressPercent < 70) return 'from-yellow-500 to-green-400'
    return 'from-green-400 to-emerald-500'
  }

  return (
    <div className="card p-0 overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-2">
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-10 flex flex-col justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-white/40 mb-6">Processing</p>
            <h2 className="text-4xl font-bold mb-4 text-white">
              {status.status === 'error' ? 'Proses Gagal' : 'Sedang Mengolah Video'}
            </h2>
            <p className="text-white/70 text-lg max-w-xl">
              {status.message || 'Menjalankan analisis video, audio, dan memotong klip terbaik untukmu.'}
            </p>
          </div>

          <div className="mt-12 space-y-8">
            <div className="relative w-48 h-48 mx-auto">
              <svg className="absolute inset-0" viewBox="0 0 160 160">
                <circle cx="80" cy="80" r="70" stroke="rgba(255,255,255,0.1)" strokeWidth="12" fill="none" />
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  strokeWidth="12"
                  strokeLinecap="round"
                  stroke="url(#progressGradient)"
                  strokeDasharray={2 * Math.PI * 70}
                  strokeDashoffset={2 * Math.PI * 70 * (1 - progressPercent / 100)}
                  fill="none"
                  transform="rotate(-90 80 80)"
                />
                <defs>
                  <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#a855f7" />
                    <stop offset="100%" stopColor="#22d3ee" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-5xl font-black text-white">{progressPercent}%</span>
                <span className="text-white/50 text-sm">proses</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm text-white/70">
              <div className="glass rounded-xl p-4 border border-white/10">
                <p className="text-xs uppercase tracking-wide text-white/40">Video</p>
                <p className="text-base font-semibold text-white mt-1 break-all">{filename}</p>
              </div>
              <div className="glass rounded-xl p-4 border border-white/10">
                <p className="text-xs uppercase tracking-wide text-white/40">Durasi Target</p>
                <p className="text-base font-semibold text-white mt-1">{formatTargetDuration(settings.targetDuration)}</p>
              </div>
              <div className="glass rounded-xl p-4 border border-white/10">
                <p className="text-xs uppercase tracking-wide text-white/40">Bahasa</p>
                <p className="text-base font-semibold text-white mt-1">{settings.language.toUpperCase()}</p>
              </div>
              <div className="glass rounded-xl p-4 border border-white/10">
                <p className="text-xs uppercase tracking-wide text-white/40">Gaya</p>
                <p className="text-base font-semibold text-white mt-1 capitalize">{settings.style}</p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={onCancel}
                className="btn-secondary w-full text-sm py-3"
              >
                {status.status === 'error' ? 'Kembali & Coba Lagi' : 'Batalkan & Kembali' }
              </button>
            </div>
          </div>
        </div>

        <div className="p-10 space-y-8">
          <section>
            <p className="text-sm font-semibold text-white/60 mb-3">Tahapan Proses</p>
            <div className="grid sm:grid-cols-2 gap-4">
              {progressSteps.map((step) => {
                const reached = progressPercent >= step.threshold
                return (
                  <div
                    key={step.key}
                    className={`rounded-2xl p-4 border transition ${
                      reached ? 'border-primary-400/70 bg-primary-400/10 shadow-lg shadow-primary-500/20' : 'border-white/10 bg-white/5'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-3xl">{step.icon}</div>
                      <div>
                        <p className="text-sm font-semibold">{step.label}</p>
                        <p className="text-xs text-white/50">
                          {reached ? '✓ Selesai' : 'Sedang diproses'}
                        </p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>

          <section>
            <p className="text-sm font-semibold text-white/60 mb-3">Aktivitas Terbaru</p>
            <div className="bg-black/30 rounded-2xl border border-white/5 h-64 overflow-y-auto p-4 space-y-3">
              {eventLog.length === 0 && (
                <p className="text-white/30 text-sm">Menunggu update status dari backend...</p>
              )}
              {eventLog.map((event) => (
                <div key={`${event.timestamp}-${event.message}`} className="flex items-start gap-3">
                  <span className="text-primary-300 text-xs mt-1">
                    {new Date(event.timestamp).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <p className="text-sm text-white/80 flex-1">{event.message}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-white/10 p-5 bg-white/5">
            <p className="text-sm font-semibold text-white/60 mb-2">Tips</p>
            <ul className="text-white/70 text-sm space-y-1 list-disc list-inside">
              <li>Jangan tutup tab ini sampai proses selesai.</li>
              <li>Proses file panjang bisa memakan waktu 5-15 menit.</li>
              <li>Setelah selesai, kamu bisa langsung preview & download semua klip.</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  )
}

function formatTargetDuration(target) {
  const mapping = {
    short: '9-15 detik',
    medium: '18-22 detik',
    long: '28-32 detik',
    all: 'Semua durasi'
  }
  return mapping[target] || target
}

export default ProcessingStatus
