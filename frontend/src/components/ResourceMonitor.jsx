import { useEffect, useState } from 'react'

const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const index = Math.min(Math.floor(Math.log(bytes || 1) / Math.log(1024)), units.length - 1)
  const value = bytes / Math.pow(1024, index)
  return `${value.toFixed(1)} ${units[index]}`
}

const processRow = (proc) => (
  <div key={proc.pid} className="flex justify-between text-sm py-1 border-b border-white/5 last:border-b-0">
    <span className="text-white/70">{proc.name || 'unknown'} (PID {proc.pid})</span>
    <span className="font-semibold">
      {(typeof proc.cpu_percent === 'number' ? proc.cpu_percent.toFixed(1) : '-')}% ·
      {' '}
      {(typeof proc.memory_mb === 'number' ? proc.memory_mb.toFixed(1) : proc.memory_mb)} MB
    </span>
  </div>
)

export default function ResourceMonitor() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    const fetchStats = async () => {
      try {
        const response = await fetch('/api/system-stats')
        if (!response.ok) {
          throw new Error('Gagal mengambil data sistem')
        }
        const data = await response.json()
        if (!cancelled) {
          setStats(data)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message)
        }
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 10000)

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const totalMem = stats?.memory?.total_bytes || 0
  const usedMem = stats?.memory?.used_bytes || 0
  const memPercent = typeof stats?.memory?.percent === 'number'
    ? stats.memory.percent.toFixed(1)
    : stats?.memory?.percent
  const cpuPercent = typeof stats?.cpu_percent === 'number'
    ? stats.cpu_percent.toFixed(1)
    : stats?.cpu_percent
  const pythonProcs = (stats?.python_processes || []).slice(0, 3)
  const nodeProcs = (stats?.node_processes || []).slice(0, 3)

  return (
    <div className="card">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <div>
          <h3 className="text-xl font-semibold">Status Laptop</h3>
          <p className="text-white/60 text-sm">Monitor CPU & RAM saat proses berjalan</p>
        </div>
        <span className="text-white/50 text-sm">
          {stats?.timestamp ? new Date(stats.timestamp).toLocaleTimeString() : 'Mengumpulkan data...'}
        </span>
      </div>

      {error ? (
        <p className="text-red-400 text-sm">{error}</p>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-sm text-white/60">CPU Total</p>
              <p className="text-2xl font-bold">{stats ? `${cpuPercent || '-'}%` : '...'}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-sm text-white/60">Memori Digunakan</p>
              <p className="text-2xl font-bold">{formatBytes(usedMem)}</p>
              <p className="text-sm text-white/60">{memPercent || '-'}% dari {formatBytes(totalMem)}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-sm text-white/60">Memori Tersedia</p>
              <p className="text-2xl font-bold">{formatBytes(stats?.memory?.available_bytes)}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-semibold mb-2">Proses Python</p>
              <div className="bg-white/5 rounded-lg p-3">
                {pythonProcs.length === 0 ? (
                  <p className="text-sm text-white/60">Tidak ada proses aktif</p>
                ) : (
                  pythonProcs.map(processRow)
                )}
              </div>
            </div>
            <div>
              <p className="text-sm font-semibold mb-2">Proses Node</p>
              <div className="bg-white/5 rounded-lg p-3">
                {nodeProcs.length === 0 ? (
                  <p className="text-sm text-white/60">Tidak ada proses aktif</p>
                ) : (
                  nodeProcs.map(processRow)
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
