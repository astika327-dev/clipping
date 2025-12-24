import { useState } from 'react'
import { Menu, X } from 'lucide-react'

function Navbar({ currentPage, onPageChange }) {
  const [isOpen, setIsOpen] = useState(false)

  const pages = [
    { id: 'home', label: 'Home', icon: '🏠' },
    { id: 'clips', label: 'Clips', icon: '✂️' },
    { id: 'storage', label: 'Storage', icon: '💾' },
    { id: 'gallery', label: 'Gallery', icon: '🖼️' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ]

  const handleNavClick = (pageId) => {
    onPageChange(pageId)
    setIsOpen(false)
  }

  return (
    <nav className="sticky top-0 z-50 bg-dark-900/80 backdrop-blur-xl border-b border-white/5">
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
              className="flex items-center gap-3 group"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-xl shadow-glow group-hover:scale-105 transition-transform duration-300">
                🎬
              </div>
              <span className="text-xl font-bold text-white hidden sm:block">
                AI <span className="text-gradient">Clipper</span>
              </span>
            </a>
          </div>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-1 p-1 rounded-xl bg-white/[0.03] border border-white/[0.05]">
            {pages.map((page) => (
              <button
                key={page.id}
                onClick={() => handleNavClick(page.id)}
                className={`
                  relative px-4 py-2 rounded-lg font-medium text-sm
                  transition-all duration-300 ease-out
                  ${currentPage === page.id
                    ? 'text-white'
                    : 'text-white/50 hover:text-white/80'
                  }
                `}
              >
                {/* Active indicator background */}
                {currentPage === page.id && (
                  <div className="absolute inset-0 bg-gradient-to-r from-primary-500/20 to-accent-500/20 rounded-lg border border-primary-500/30" />
                )}
                <span className="relative flex items-center gap-2">
                  <span>{page.icon}</span>
                  <span>{page.label}</span>
                </span>
              </button>
            ))}
          </div>

          {/* Status Badge */}
          <div className="hidden md:flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-emerald-400 text-xs font-medium">Online</span>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-xl text-white/70 hover:text-white hover:bg-white/5 transition-all duration-300"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <div className={`md:hidden overflow-hidden transition-all duration-300 ease-out ${isOpen ? 'max-h-96' : 'max-h-0'}`}>
        <div className="px-4 pt-2 pb-4 space-y-1 bg-dark-800/50 backdrop-blur-xl border-t border-white/5">
          {pages.map((page) => (
            <button
              key={page.id}
              onClick={() => handleNavClick(page.id)}
              className={`
                block w-full text-left px-4 py-3 rounded-xl font-medium
                transition-all duration-300
                ${currentPage === page.id
                  ? 'bg-gradient-to-r from-primary-500/20 to-accent-500/10 text-white border border-primary-500/30'
                  : 'text-white/60 hover:text-white hover:bg-white/5'
                }
              `}
            >
              <span className="flex items-center gap-3">
                <span className="text-lg">{page.icon}</span>
                <span>{page.label}</span>
              </span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
