function SettingsPanel({ settings, onSettingsChange, onProcessStart, uploadedVideo, isProcessing }) {
  const handleProcess = () => {
    if (isProcessing) return
    onProcessStart?.()
  }

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-6">Pengaturan Klip</h2>

      <div className="space-y-6">
        {/* Language */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Bahasa Video
          </label>
          <select
            value={settings.language}
            onChange={(e) => onSettingsChange({ ...settings, language: e.target.value })}
            className="input-field"
          >
            <option value="id">🇮🇩 Bahasa Indonesia</option>
            <option value="en">🇬🇧 English</option>
          </select>
          <p className="text-white/50 text-xs mt-1">
            Pilih bahasa untuk transkripsi yang lebih akurat
          </p>
        </div>

        {/* Target Duration */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Durasi Target Klip
          </label>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { value: 'short', label: '9-15 detik', emoji: '⚡' },
              { value: 'medium', label: '18-22 detik', emoji: '🎯' },
              { value: 'long', label: '28-32 detik', emoji: '📺' },
              { value: 'extended', label: '40-50 detik', emoji: '🎞️' },
              { value: 'all', label: 'Semua', emoji: '🎬' }
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => onSettingsChange({ ...settings, targetDuration: option.value })}
                className={`
                  p-3 rounded-lg border-2 transition-all
                  ${settings.targetDuration === option.value
                    ? 'border-primary-500 bg-primary-500/20'
                    : 'border-white/20 hover:border-white/40'
                  }
                `}
              >
                <div className="text-2xl mb-1">{option.emoji}</div>
                <div className="text-sm font-medium">{option.label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Style */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Gaya Konten
          </label>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { value: 'balanced', label: 'Seimbang', emoji: '⚖️' },
              { value: 'funny', label: 'Lucu', emoji: '😂' },
              { value: 'educational', label: 'Edukasi', emoji: '📚' },
              { value: 'dramatic', label: 'Dramatis', emoji: '🎭' },
              { value: 'controversial', label: 'Opini Keras', emoji: '🔥' }
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => onSettingsChange({ ...settings, style: option.value })}
                className={`
                  p-3 rounded-lg border-2 transition-all
                  ${settings.style === option.value
                    ? 'border-accent-500 bg-accent-500/20'
                    : 'border-white/20 hover:border-white/40'
                  }
                `}
              >
                <div className="text-2xl mb-1">{option.emoji}</div>
                <div className="text-xs font-medium">{option.label}</div>
              </button>
            ))}
          </div>
          <p className="text-white/50 text-xs mt-2">
            AI akan prioritaskan klip yang sesuai dengan gaya yang dipilih
          </p>
        </div>

        {/* Resolution */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Resolusi Output
          </label>
          <div className="grid grid-cols-2 gap-3">
            {[
              { value: '720p', label: '720p', description: 'File lebih kecil', emoji: '📱' },
              { value: '1080p', label: '1080p', description: 'Kualitas tinggi', emoji: '🖥️' }
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => onSettingsChange({ ...settings, resolution: option.value })}
                className={`
                  p-3 rounded-lg border-2 transition-all
                  ${settings.resolution === option.value
                    ? 'border-green-500 bg-green-500/20'
                    : 'border-white/20 hover:border-white/40'
                  }
                `}
              >
                <div className="text-2xl mb-1">{option.emoji}</div>
                <div className="text-sm font-medium">{option.label}</div>
                <div className="text-[10px] text-white/60">{option.description}</div>
              </button>
            ))}
          </div>
          <p className="text-white/50 text-xs mt-2">
            720p: export lebih cepat & file kecil. 1080p: kualitas maksimal.
          </p>
        </div>

        {/* Hooks & Caption */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="glass rounded-xl p-4 border border-white/10">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold mb-1">Hook ala Timoty Ronald</p>
                <p className="text-xs text-white/60">
                  AI bikin kalimat pembuka yang nendang ala video Timoty buat setiap klip
                </p>
              </div>
              <label className="inline-flex items-center cursor-pointer select-none">
                <div className="relative">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={settings.useTimotyHook}
                    onChange={(e) => onSettingsChange({ ...settings, useTimotyHook: e.target.checked })}
                  />
                  <div className="w-12 h-6 bg-white/20 rounded-full peer peer-checked:bg-primary-500 transition-colors"></div>
                  <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-6"></div>
                </div>
                <span className="ml-3 text-xs font-semibold text-white/70">
                  {settings.useTimotyHook ? 'ON' : 'OFF'}
                </span>
              </label>
            </div>
          </div>
          <div className="glass rounded-xl p-4 border border-white/10">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold mb-1">Auto Caption (SRT)</p>
                <p className="text-xs text-white/60">
                  Generate file caption otomatis yang bisa langsung dipakai di TikTok/CapCut
                </p>
              </div>
              <label className="inline-flex items-center cursor-pointer select-none">
                <div className="relative">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={settings.autoCaption}
                    onChange={(e) => onSettingsChange({ ...settings, autoCaption: e.target.checked })}
                  />
                  <div className="w-12 h-6 bg-white/20 rounded-full peer peer-checked:bg-accent-500 transition-colors"></div>
                  <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-6"></div>
                </div>
                <span className="ml-3 text-xs font-semibold text-white/70">
                  {settings.autoCaption ? 'ON' : 'OFF'}
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Process Button */}
        <button
          type="button"
          onClick={handleProcess}
          disabled={isProcessing}
          className="btn-primary w-full text-lg py-4"
        >
          {isProcessing ? (
            <span className="flex items-center justify-center">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
              Processing...
            </span>
          ) : (
            <span className="flex items-center justify-center">
              <span className="mr-2">✨</span>
              Generate Klip Sekarang
            </span>
          )}
        </button>
      </div>

      {/* Info */}
      <div className="mt-6 p-4 glass rounded-lg">
        <h3 className="font-semibold mb-2 flex items-center">
          <span className="mr-2">ℹ️</span>
          Estimasi Waktu Proses
        </h3>
        <p className="text-white/70 text-sm">
          Video {Math.floor(uploadedVideo.duration / 60)} menit akan diproses dalam{' '}
          <span className="font-semibold text-primary-400">
            ~{Math.ceil(uploadedVideo.duration / 60 * 2)}-{Math.ceil(uploadedVideo.duration / 60 * 5)} menit
          </span>
          {' '}tergantung kompleksitas konten.
        </p>
      </div>
    </div>
  )
}

export default SettingsPanel
