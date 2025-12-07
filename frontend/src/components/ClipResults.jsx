import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

function ClipResults({ clips, jobId, onReset }) {
  const [selectedClip, setSelectedClip] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [clipList, setClipList] = useState(Array.isArray(clips) ? clips : [])
  const [loadingClips, setLoadingClips] = useState(false)
  const fetchedRef = useRef(false)

  useEffect(() => {
    setClipList(Array.isArray(clips) ? clips : [])
    if (Array.isArray(clips) && clips.length > 0) {
      fetchedRef.current = true
    } else if (Array.isArray(clips) && clips.length === 0) {
      fetchedRef.current = false
    }
  }, [clips])

  useEffect(() => {
    if (fetchedRef.current) return
    if (!jobId) return
    setLoadingClips(true)
    axios.get(`/api/status/${jobId}`)
      .then(({ data }) => {
        if (Array.isArray(data?.clips) && data.clips.length > 0) {
          setClipList(data.clips)
          fetchedRef.current = true
        }
      })
      .catch((error) => {
        console.error('Fetch clips fallback error:', error)
      })
      .finally(() => setLoadingClips(false))
  }, [jobId])

  const getViralBadge = (score) => {
    if (!score) return 'badge-info'
    if (score === 'Tinggi' || score === 'High') return 'badge-success'
    if (score === 'Sedang' || score === 'Medium') return 'badge-warning'
    return 'badge-danger'
  }

  const getCategoryEmoji = (category) => {
    const emojis = {
      educational: '📚',
      entertaining: '😂',
      emotional: '❤️',
      controversial: '🔥',
      balanced: '⚖️',
      funny: '😂',
      dramatic: '🎭'
    }
    return emojis[category] || '🎬'
  }

  const downloadAsset = async (assetName, label) => {
    if (!assetName) return
    try {
      const response = await axios.get(`/api/download/${jobId}/${assetName}`, {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', assetName)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error(`Download ${label} error:`, error)
      alert(`Gagal download ${label}`)
    }
  }

  const handleDownloadClip = async (clip) => downloadAsset(clip.filename, 'klip')
  const handleDownloadCaption = async (clip) => downloadAsset(clip.caption_file, 'caption')

  const handleCopyHook = async (hookText) => {
    if (!hookText) return
    if (typeof navigator === 'undefined' || !navigator.clipboard) {
      alert('Clipboard tidak tersedia')
      return
    }
    try {
      await navigator.clipboard.writeText(hookText)
    } catch (error) {
      console.error('Copy hook error:', error)
      alert('Clipboard tidak tersedia')
    }
  }

  const handleDownloadAll = async () => {
    setDownloading(true)
    try {
      const response = await axios.get(`/api/download-all/${jobId}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${jobId}_clips.zip`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Download all error:', error)
      alert('Gagal download semua klip')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div id="clip-results" className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold mb-2">
              🎉 Klip Berhasil Dibuat!
            </h2>
            <p className="text-white/70">
              {clipList.length} klip siap untuk di-upload ke TikTok
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleDownloadAll}
              disabled={downloading}
              className="btn-primary"
            >
              {downloading ? (
                <span className="flex items-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Downloading...
                </span>
              ) : (
                <span className="flex items-center">
                  <span className="mr-2">📦</span>
                  Download Semua
                </span>
              )}
            </button>
            <button
              onClick={onReset}
              className="btn-secondary"
            >
              Upload Baru
            </button>
          </div>
        </div>
      </div>

      {/* Clips Grid */}
      {loadingClips && clipList.length === 0 && (
        <div className="card text-center text-white/60">
          Sedang memuat daftar klip dari server...
        </div>
      )}

      {!loadingClips && clipList.length === 0 && (
        <div className="card text-center text-white/60">
          Belum ada klip untuk job ini. Silakan proses ulang atau cek log backend.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clipList.map((clip) => (
          <div
            key={clip.id}
            className="card-hover group"
            onClick={() => setSelectedClip(clip)}
          >
            {/* Clip Preview */}
            <div className="relative aspect-[9/16] bg-black/50 rounded-lg mb-4 overflow-hidden">
              <video
                src={`/api/preview/${jobId}/${clip.filename}`}
                className="w-full h-full object-cover"
                controls={false}
                onMouseEnter={(e) => e.target.play()}
                onMouseLeave={(e) => {
                  e.target.pause()
                  e.target.currentTime = 0
                }}
              />
              
              {/* Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="absolute bottom-0 left-0 right-0 p-4">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDownloadClip(clip)
                    }}
                    className="btn-primary w-full text-sm py-2"
                  >
                    📥 Download
                  </button>
                </div>
              </div>

              {/* Duration Badge */}
              <div className="absolute top-2 right-2 px-2 py-1 bg-black/70 rounded text-xs font-medium">
                {Math.floor(clip.duration || 0)}s
              </div>
            </div>

            {/* Clip Info */}
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold mb-1 line-clamp-2">
                  {clip.title || `Clip ${clip.id}`}
                </h3>
                <p className="text-xs text-white/60">
                  {clip.start_time || '0:00'} - {clip.end_time || '0:00'}
                </p>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <span className={getViralBadge(clip.viral_score)}>
                  {clip.viral_score || 'N/A'}
                </span>
                <span className="badge-info">
                  {getCategoryEmoji(clip.category)} {clip.category || 'general'}
                </span>
                {clip.caption_file && (
                  <span className="px-2 py-0.5 text-[10px] rounded border border-white/20 text-white/70">
                    📝 Caption
                  </span>
                )}
              </div>

              <p className="text-xs text-white/70 line-clamp-2">
                💡 {clip.reason || 'Klip terpilih'}
              </p>
              {clip.timoty_hook && (
                <p className="text-xs text-primary-200 line-clamp-2">
                  🔥 {clip.timoty_hook.text}
                </p>
              )}
              {clip.caption_file && clip.caption_preview && (
                <p className="text-[11px] text-white/50 line-clamp-1">
                  📝 {clip.caption_preview}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Selected Clip Modal */}
      {selectedClip && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedClip(null)}
        >
          <div
            className="card max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-2xl font-bold">Clip #{selectedClip.id}</h3>
              <button
                onClick={() => setSelectedClip(null)}
                className="text-white/60 hover:text-white text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Video Player */}
              <div>
                <video
                  src={`/api/preview/${jobId}/${selectedClip.filename}`}
                  className="w-full rounded-lg"
                  controls
                  autoPlay
                />
                <button
                  onClick={() => handleDownloadClip(selectedClip)}
                  className="btn-primary w-full mt-4"
                >
                  📥 Download Klip Ini
                </button>
              </div>

              {/* Details */}
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Informasi Klip</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-white/60">Durasi:</span>
                      <span className="font-medium">{Math.floor(selectedClip.duration)} detik</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">Timestamp:</span>
                      <span className="font-medium">
                        {selectedClip.start_time} - {selectedClip.end_time}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">Kategori:</span>
                      <span className="font-medium">
                        {getCategoryEmoji(selectedClip.category)} {selectedClip.category}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">Potensi Viral:</span>
                      <span className={getViralBadge(selectedClip.viral_score)}>
                        {selectedClip.viral_score} ({selectedClip.viral_score_numeric})
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Alasan Skor</h4>
                  <p className="text-sm text-white/70">
                    {selectedClip.reason}
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Transkrip</h4>
                  <div className="p-3 glass rounded-lg text-sm text-white/80 max-h-40 overflow-y-auto">
                    {selectedClip.transcript}
                  </div>
                </div>

                {selectedClip.timoty_hook && (
                  <div className="p-4 glass rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold">Hook Timoty Ronald</h4>
                      <span className="text-xs text-white/60">
                        {selectedClip.timoty_hook.theme} • conf {selectedClip.timoty_hook.confidence}
                      </span>
                    </div>
                    <p className="text-sm text-primary-100 leading-relaxed">
                      {selectedClip.timoty_hook.text}
                    </p>
                    {selectedClip.timoty_hook.power_words?.length > 0 && (
                      <p className="text-[11px] text-white/50">
                        Power words: {selectedClip.timoty_hook.power_words.join(', ')}
                      </p>
                    )}
                    <button
                      onClick={() => handleCopyHook(selectedClip.timoty_hook.text)}
                      className="btn-secondary w-full text-sm"
                    >
                      📋 Copy Hook
                    </button>
                  </div>
                )}

                {selectedClip.caption_file && (
                  <div className="p-4 glass rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold">Auto Caption</h4>
                      <span className="text-xs text-white/60">
                        {selectedClip.captions?.length || 0} baris
                      </span>
                    </div>
                    <div className="text-xs text-white/70 max-h-32 overflow-y-auto space-y-2">
                      {(selectedClip.captions || []).slice(0, 4).map((line) => (
                        <div key={line.index} className="border border-white/10 rounded p-2">
                          <p className="text-[10px] text-white/50">
                            {line.start} - {line.end}
                          </p>
                          <p>{line.text}</p>
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={() => handleDownloadCaption(selectedClip)}
                      className="btn-secondary w-full text-sm"
                    >
                      📝 Download SRT
                    </button>
                  </div>
                )}

                <div className="p-4 bg-primary-500/20 border border-primary-500/30 rounded-lg">
                  <h4 className="font-semibold mb-2 flex items-center">
                    <span className="mr-2">💡</span>
                    Tips Upload TikTok
                  </h4>
                  <ul className="text-xs text-white/70 space-y-1">
                    <li>• Upload di jam prime time (19:00-22:00)</li>
                    <li>• Tambahkan caption menarik</li>
                    <li>• Gunakan hashtag relevan (#fyp #viral)</li>
                    <li>• Tambahkan musik trending jika perlu</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ClipResults
