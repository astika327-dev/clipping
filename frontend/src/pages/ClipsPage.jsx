import { useEffect, useState } from 'react'
import { Download, Trash2, Play, FileText } from 'lucide-react'

function ClipsPage() {
  const [clips, setClips] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedClips, setSelectedClips] = useState(new Set())

  useEffect(() => {
    fetchAllClips()
  }, [])

  const fetchAllClips = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/clips')
      if (!response.ok) throw new Error('Gagal fetch clips')
      
      const data = await response.json()
      setClips(data.clips || [])
    } catch (error) {
      console.error('Error fetching clips:', error)
      setClips([])
    } finally {
      setLoading(false)
    }
  }

  const downloadClip = async (jobId, clipFilename) => {
    try {
      const response = await fetch(
        `/api/download/${jobId}/${clipFilename}`
      )
      if (!response.ok) throw new Error('Download gagal')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = clipFilename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading clip:', error)
      alert('Gagal download clip')
    }
  }

  const downloadAllClips = async () => {
    if (selectedClips.size === 0) {
      alert('Pilih minimal 1 clip untuk download')
      return
    }

    try {
      for (const clipId of selectedClips) {
        const clip = clips.find(c => c.id === clipId)
        if (clip) {
          await downloadClip(clip.jobId, clip.filename)
          // Delay antar download
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      }
    } catch (error) {
      console.error('Error downloading clips:', error)
    }
  }

  const deleteClip = async (jobId, clipFilename) => {
    if (!window.confirm(`Hapus clip ${clipFilename}?`)) return

    try {
      const response = await fetch(
        `/api/delete/${jobId}/${clipFilename}`,
        { method: 'DELETE' }
      )
      if (!response.ok) throw new Error('Delete gagal')

      setClips(clips.filter(c => !(c.jobId === jobId && c.filename === clipFilename)))
      setSelectedClips(new Set([...selectedClips].filter(id => id !== `${jobId}-${clipFilename}`)))
      alert('Clip berhasil dihapus')
    } catch (error) {
      console.error('Error deleting clip:', error)
      alert('Gagal hapus clip')
    }
  }

  const deleteAllClips = async () => {
    if (selectedClips.size === 0) {
      alert('Pilih minimal 1 clip untuk hapus')
      return
    }

    if (!window.confirm(`Hapus ${selectedClips.size} clip?`)) return

    try {
      for (const clipId of selectedClips) {
        const clip = clips.find(c => c.id === clipId)
        if (clip) {
          await fetch(
            `/api/delete/${clip.jobId}/${clip.filename}`,
            { method: 'DELETE' }
          )
        }
      }
      
      setClips(clips.filter(c => !selectedClips.has(c.id)))
      setSelectedClips(new Set())
      alert('Clips berhasil dihapus')
    } catch (error) {
      console.error('Error deleting clips:', error)
      alert('Gagal hapus clips')
    }
  }

  const toggleClipSelection = (clipId) => {
    const newSelected = new Set(selectedClips)
    if (newSelected.has(clipId)) {
      newSelected.delete(clipId)
    } else {
      newSelected.add(clipId)
    }
    setSelectedClips(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedClips.size === clips.length) {
      setSelectedClips(new Set())
    } else {
      setSelectedClips(new Set(clips.map(c => c.id)))
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDuration = (seconds) => {
    if (!seconds) return '--:--'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${String(secs).padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-400"></div>
        </div>
        <p className="text-white/60 mt-4">Loading clips...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
          🎬 Exported Clips
        </h1>
        <p className="text-white/60">
          {clips.length} clip{clips.length !== 1 ? 's' : ''} available
        </p>
      </div>

      {clips.length > 0 ? (
        <>
          {/* Action Bar */}
          <div className="card flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={selectedClips.size === clips.length && clips.length > 0}
                onChange={toggleSelectAll}
                className="w-5 h-5 cursor-pointer"
              />
              <span className="text-sm text-white/60">
                {selectedClips.size > 0 ? `${selectedClips.size} selected` : 'Select all'}
              </span>
            </div>

            <div className="flex gap-2 w-full sm:w-auto">
              <button
                onClick={downloadAllClips}
                disabled={selectedClips.size === 0}
                className="flex-1 sm:flex-none btn-primary gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download size={18} />
                Download All
              </button>
              <button
                onClick={deleteAllClips}
                disabled={selectedClips.size === 0}
                className="flex-1 sm:flex-none btn-danger gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Trash2 size={18} />
                Delete All
              </button>
            </div>
          </div>

          {/* Clips Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {clips.map((clip) => (
              <div
                key={clip.id}
                className={`card group cursor-pointer transition-all ${
                  selectedClips.has(clip.id)
                    ? 'ring-2 ring-primary-500 bg-primary-500/10'
                    : 'hover:ring-2 hover:ring-primary-500/30'
                }`}
              >
                {/* Checkbox Overlay */}
                <div className="absolute top-3 left-3 z-10">
                  <input
                    type="checkbox"
                    checked={selectedClips.has(clip.id)}
                    onChange={() => toggleClipSelection(clip.id)}
                    className="w-5 h-5 cursor-pointer"
                  />
                </div>

                {/* Video Preview */}
                <div className="relative bg-black rounded-lg overflow-hidden mb-4 aspect-video flex items-center justify-center group">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary-500/20 to-accent-500/20"></div>
                  <Play size={48} className="text-white/40 group-hover:text-white/70 transition" />
                </div>

                {/* Clip Info */}
                <div className="space-y-3">
                  {/* Filename */}
                  <div>
                    <h3 className="font-semibold text-white truncate" title={clip.filename}>
                      {clip.filename.replace('.mp4', '')}
                    </h3>
                    <p className="text-xs text-white/50 mt-1">
                      Job: {clip.jobId.substring(0, 12)}...
                    </p>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="bg-white/5 rounded p-2">
                      <p className="text-white/60 text-xs">Duration</p>
                      <p className="font-semibold text-primary-300">
                        {formatDuration(clip.duration)}
                      </p>
                    </div>
                    <div className="bg-white/5 rounded p-2">
                      <p className="text-white/60 text-xs">File Size</p>
                      <p className="font-semibold text-accent-300">
                        {formatFileSize(clip.size)}
                      </p>
                    </div>
                  </div>

                  {/* Metadata */}
                  {clip.metadata && (
                    <div className="bg-white/5 rounded p-2 text-xs text-white/60">
                      <div className="flex items-start gap-2">
                        <FileText size={14} className="mt-0.5 flex-shrink-0" />
                        <div>
                          <p>Codec: <span className="text-white/80">{clip.metadata.video_codec || 'H.264'}</span></p>
                          <p>Bitrate: <span className="text-white/80">{clip.metadata.bitrate || '4 Mbps'}</span></p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Export Date */}
                  <p className="text-xs text-white/40">
                    {new Date(clip.exportedAt).toLocaleString('id-ID')}
                  </p>

                  {/* Actions */}
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => downloadClip(clip.jobId, clip.filename)}
                      className="flex-1 btn-primary btn-sm gap-1.5"
                    >
                      <Download size={16} />
                      Download
                    </button>
                    <button
                      onClick={() => deleteClip(clip.jobId, clip.filename)}
                      className="flex-1 btn-danger btn-sm gap-1.5"
                    >
                      <Trash2 size={16} />
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="card text-center py-12">
          <div className="text-4xl mb-4">🎬</div>
          <h3 className="text-xl font-semibold text-white mb-2">No Clips Yet</h3>
          <p className="text-white/60 mb-6">
            Uploaded video dan proses untuk generate clips
          </p>
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              window.location.href = '/'
            }}
            className="btn-primary inline-block"
          >
            Upload Video
          </a>
        </div>
      )}
    </div>
  )
}

export default ClipsPage
