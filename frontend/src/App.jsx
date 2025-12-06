import { useState } from 'react'
import VideoUploader from './components/VideoUploader'
import SettingsPanel from './components/SettingsPanel'
import ProcessingStatus from './components/ProcessingStatus'
import ClipResults from './components/ClipResults'
import ResourceMonitor from './components/ResourceMonitor'

function App() {
  const [uploadedVideo, setUploadedVideo] = useState(null)
  const [settings, setSettings] = useState({
    language: 'id',
    targetDuration: 'all',
    style: 'balanced',
    useTimotyHook: true,
    autoCaption: false,
    transcriptionBackend: 'faster-whisper',
    modelSize: 'medium'
  })
  const [processing, setProcessing] = useState(false)
  const [uiStep, setUiStep] = useState('landing')
  const [jobId, setJobId] = useState(null)
  const [clips, setClips] = useState([])

  const handleVideoUploaded = (videoData) => {
    setUploadedVideo(videoData)
    setClips([])
    setJobId(null)
    setUiStep('ready')
  }

  const startProcessing = () => {
    if (!uploadedVideo) return
    const derivedJobId = uploadedVideo.filename.replace(/\./g, '_')
    setJobId(derivedJobId)
    setProcessing(true)
    setUiStep('processing')
  }

  const handleProcessComplete = (result) => {
    setJobId(result.job_id)
    setClips(result.clips || [])
    setProcessing(false)
    setUiStep('results')
  }

  const handleReset = () => {
    setUploadedVideo(null)
    setClips([])
    setJobId(null)
    setProcessing(false)
    setUiStep('landing')
  }

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
            🎬 AI Video Clipper
          </h1>
          <p className="text-xl text-white/70">
            Otomatis potong video panjang jadi klip pendek viral untuk TikTok, Reels & Shorts
          </p>
        </header>

        {/* Main Content */}
        <div className="space-y-8">
          <ResourceMonitor />
          {uiStep === 'landing' && (
            <VideoUploader onVideoUploaded={handleVideoUploaded} />
          )}

          {uiStep === 'ready' && uploadedVideo && (
            <>
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold">Video Uploaded</h3>
                    <p className="text-white/60 text-sm mt-1">
                      {uploadedVideo.filename}
                    </p>
                  </div>
                  <button
                    onClick={handleReset}
                    className="btn-secondary"
                  >
                    Upload Baru
                  </button>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-white/60">Ukuran:</span>
                    <span className="ml-2 font-medium">
                      {(uploadedVideo.size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  </div>
                  <div>
                    <span className="text-white/60">Durasi:</span>
                    <span className="ml-2 font-medium">
                      {Math.floor(uploadedVideo.duration / 60)}:{String(Math.floor(uploadedVideo.duration % 60)).padStart(2, '0')}
                    </span>
                  </div>
                  <div>
                    <span className="text-white/60">Status:</span>
                    <span className="ml-2 badge-success">Siap Diproses</span>
                  </div>
                </div>
                {uploadedVideo.source === 'youtube' && (
                  <div className="mt-4 glass rounded-lg p-4 text-sm">
                    <p className="font-semibold flex items-center gap-2">
                      <span>📺</span>
                      Konten dari YouTube
                    </p>
                    <p className="text-white/70 mt-1">
                      {uploadedVideo.title || 'Tanpa judul'}
                      {uploadedVideo.channel ? ` • ${uploadedVideo.channel}` : ''}
                    </p>
                    <p className="text-white/50 text-xs mt-1 break-all">{uploadedVideo.url}</p>
                  </div>
                )}
              </div>

              <SettingsPanel
                settings={settings}
                onSettingsChange={setSettings}
                onProcessStart={startProcessing}
                isProcessing={processing}
                uploadedVideo={uploadedVideo}
              />
            </>
          )}

          {uiStep === 'processing' && uploadedVideo && jobId && (
            <ProcessingStatus
              filename={uploadedVideo.filename}
              jobId={jobId}
              settings={settings}
              onComplete={handleProcessComplete}
              onCancel={() => {
                setProcessing(false)
                setUiStep('ready')
              }}
            />
          )}

          {uiStep === 'results' && (
            <ClipResults
              clips={clips}
              jobId={jobId}
              onReset={handleReset}
            />
          )}
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center text-white/40 text-sm">
          <p>Dibuat dengan ❤️ untuk content creators Indonesia</p>
        </footer>
      </div>
    </div>
  )
}

export default App
