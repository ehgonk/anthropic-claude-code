import { Sun, Moon, Monitor, ChevronDown } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

export type ThemeMode = 'system' | 'light' | 'dark'

interface ThemeSwitcherProps {
  currentTheme: ThemeMode
  onThemeChange: (theme: ThemeMode) => void
}

export default function ThemeSwitcher({ currentTheme, onThemeChange }: ThemeSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  console.log('🎨 ThemeSwitcher rendered, currentTheme:', currentTheme)

  const themes = [
    { id: 'system' as const, label: 'Padrão Sistema', icon: Monitor },
    { id: 'light' as const, label: 'Claro', icon: Sun },
    { id: 'dark' as const, label: 'Dark', icon: Moon },
  ]

  const currentThemeData = themes.find(t => t.id === currentTheme) || themes[0]
  const CurrentIcon = currentThemeData.icon

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => {
          console.log('🎨 Theme button clicked, isOpen:', !isOpen)
          setIsOpen(!isOpen)
        }}
        className="flex items-center gap-1.5 px-3 py-2 rounded hover:bg-dark-border transition-colors border border-dark-border"
        title="Alterar tema"
      >
        <CurrentIcon className="w-4 h-4 text-dark-text" />
        <span className="text-sm text-dark-text">{currentThemeData.label}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-dark-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-48 bg-dark-card border border-dark-border rounded-lg shadow-2xl z-50">
          {themes.map((theme) => {
            const Icon = theme.icon
            const isActive = currentTheme === theme.id

            return (
              <button
                key={theme.id}
                onClick={() => {
                  onThemeChange(theme.id)
                  setIsOpen(false)
                }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors first:rounded-t-lg last:rounded-b-lg ${
                  isActive
                    ? 'bg-blue-500/20 text-dark-text'
                    : 'text-dark-muted hover:bg-dark-border hover:text-dark-text'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-dark-muted'}`} />
                <span className="flex-1 text-left">{theme.label}</span>
                {isActive && (
                  <div className="w-2 h-2 rounded-full bg-blue-400" />
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
