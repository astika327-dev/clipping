import { useState, useEffect } from 'react'
import { Trash2, RefreshCw } from 'lucide-react'

function StoragePage() {
  const [storageData, setStorageData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchStorageInfo()
  }, [])

  const fetchStorageInfo = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:5000/api/storage')
      const data = await response.json()
      setStorageData(data)
    } catch (error) {
      console.error('Error fetching storage info:', error)
      setMessage('Error loading storage info')
    } finally {
      setLoading(false)
    }
  }

  const deleteFile = async (filename) => {
    if (!window.confirm(`Delete ${filename}?`)) return

    try {
      setDeleting(true)
      const response = await fetch(
        `http://localhost:5000/api/upload/${encodeURIComponent(filename)}`,
        { method: 'DELETE' }
      )
      const result = await response.json()

      if (response.ok) {
        setMessage(`✅ Deleted: ${filename}`)
        setTimeout(() => fetchStorageInfo(), 500)
      } else {
        setMessage(`❌ ${result.error}`)
      }
    } catch (error) {
      console.error('Error deleting file:', error)
      setMessage('Error deleting file')
    } finally {
      setDeleting(false)
    }
  }

  const deleteAllUploads = async () => {
    if (!window.confirm('⚠️ Delete ALL uploaded videos? This cannot be undone!')) return

    try {
      setDeleting(true)
      const response = await fetch('http://localhost:5000/api/upload/delete-all', {
        method: 'POST'
      })
      const result = await response.json()

      if (response.ok) {
        setMessage(`✅ Deleted ${result.deleted_count} files`)
        setTimeout(() => fetchStorageInfo(), 500)
      } else {
        setMessage(`❌ ${result.error}`)
      }
    } catch (error) {
      console.error('Error deleting files:', error)
      setMessage('Error deleting files')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">💾 Storage Management</h2>
        <button
          onClick={fetchStorageInfo}
          disabled={loading}
          className="btn-primary flex items-center gap-2"
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {message && (
        <div className="card bg-accent-900/30 border border-accent-500/30 p-4">
          {message}
        </div>
      )}

      {loading ? (
        <div className="card text-center py-12">
          <p className="text-white/60">Loading storage info...</p>
        </div>
      ) : storageData ? (
        <>
          {/* Storage Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Uploads */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">📤 Uploaded Videos</h3>
              <div className="space-y-2">
                <p className="text-white/70">
                  <span className="font-semibold text-white">{storageData.uploads.total_gb}</span> GB
                </p>
                <p className="text-sm text-white/50">
                  ({storageData.uploads.total_mb} MB)
                </p>
                <p className="text-sm text-white/50">
                  {storageData.uploads.files?.length || 0} files
                </p>
              </div>
            </div>

            {/* Outputs */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">📥 Generated Clips</h3>
              <div className="space-y-2">
                <p className="text-white/70">
                  <span className="font-semibold text-white">{storageData.outputs.total_gb}</span> GB
                </p>
                <p className="text-sm text-white/50">
                  ({storageData.outputs.total_mb} MB)
                </p>
              </div>
            </div>
          </div>

          {/* Upload Files List */}
          {storageData.uploads.files && storageData.uploads.files.length > 0 && (
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">File List</h3>
                <button
                  onClick={deleteAllUploads}
                  disabled={deleting}
                  className="btn-danger text-sm"
                >
                  <Trash2 size={16} className="inline mr-2" />
                  Delete All
                </button>
              </div>

              <div className="space-y-2 max-h-96 overflow-y-auto">
                {storageData.uploads.files.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-mono text-sm text-white/80 truncate">
                        {file.filename}
                      </p>
                      <p className="text-xs text-white/50 mt-1">
                        {file.size_mb} MB
                      </p>
                    </div>
                    <button
                      onClick={() => deleteFile(file.filename)}
                      disabled={deleting}
                      className="btn-danger text-sm ml-2 flex-shrink-0"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(!storageData.uploads.files || storageData.uploads.files.length === 0) && (
            <div className="card text-center py-8 text-white/60">
              <p>No uploaded videos</p>
            </div>
          )}
        </>
      ) : (
        <div className="card text-center py-12 text-white/60">
          Error loading storage info
        </div>
      )}
    </div>
  )
}

export default StoragePage
