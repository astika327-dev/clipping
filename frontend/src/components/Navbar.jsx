import { useState } from 'react'
import { Menu, X } from 'lucide-react'

function Navbar({ currentPage, onPageChange }) {
  const [isOpen, setIsOpen] = useState(false)

  const pages = [
    { id: 'home', label: '🎬 Home', path: '/' },
    { id: 'storage', label: '💾 Storage', path: '/storage' },
    { id: 'gallery', label: '🖼️ Gallery', path: '/gallery' },
    { id: 'settings', label: '⚙️ Settings', path: '/settings' },
  ]

  const handleNavClick = (pageId) => {
    onPageChange(pageId)
    setIsOpen(false)
  }

  return (
    <nav className="bg-gradient-to-r from-slate-900 to-slate-800 shadow-lg border-b border-primary-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <a 
              href="#" 
              onClick={(e) => {
                e.preventDefault()
                handleNavClick('home')
              }}
              className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent hover:opacity-80 transition"
            >
              🎬 AI Clipper
            </a>
          </div>

          {/* Desktop Menu */}
          <div className="hidden md:flex space-x-1">
            {pages.map((page) => (
              <button
                key={page.id}
                onClick={() => handleNavClick(page.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  currentPage === page.id
                    ? 'bg-primary-500/30 text-primary-300 border border-primary-400/50'
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                {page.label}
              </button>
            ))}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-slate-800/50 backdrop-blur-sm border-t border-primary-500/20">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {pages.map((page) => (
              <button
                key={page.id}
                onClick={() => handleNavClick(page.id)}
                className={`block w-full text-left px-3 py-2 rounded-md font-medium transition-all ${
                  currentPage === page.id
                    ? 'bg-primary-500/30 text-primary-300'
                    : 'text-white/70 hover:text-white hover:bg-white/5'
                }`}
              >
                {page.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </nav>
  )
}

export default Navbar
