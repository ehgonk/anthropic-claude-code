import { Menu, Settings, Bell, Database, Sun, Moon } from 'lucide-react'
import type { Stock } from '../App'

interface TopBarProps {
  selectedStock: Stock | null
  lastB3Date: string | null
  isUpdating: boolean
  updateMessage: string | null
  isDark: boolean
  onToggleTheme: () => void
}

export default function TopBar({ selectedStock, lastB3Date, isUpdating, updateMessage, isDark, onToggleTheme }: TopBarProps) {
  const formatDate = (dateStr: string) => {
    const [year, month, day] = dateStr.split('-')
    return `${day}/${month}/${year}`
  }

  return (
    <div className="h-12 bg-dark-card border-b border-dark-border flex items-center justify-between px-4">
      <div className="flex items-center gap-4">
        <button className="p-1 hover:bg-dark-border rounded">
          <Menu className="w-5 h-5 text-dark-muted" />
        </button>

        <span className="text-lg font-bold text-dark-text">Broker</span>

        {selectedStock && (
          <div className="flex items-center gap-3 ml-4 pl-4 border-l border-dark-border">
            <div className="flex items-center gap-2">
              <span className="text-dark-text font-semibold">{selectedStock.symbol}</span>
              <span className="text-xl font-bold text-dark-text">
                R$ {selectedStock.price.toFixed(2)}
              </span>
              <span className={`text-sm font-semibold ${
                selectedStock.change_percent >= 0 ? 'text-green-profit' : 'text-red-loss'
              }`}>
                {selectedStock.change_percent >= 0 ? '+' : ''}
                {selectedStock.change_percent.toFixed(2)}%
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Update status message */}
        {isUpdating && updateMessage && (
          <div className="flex items-center gap-2 px-3 py-1 bg-blue-900/30 border border-blue-700/50 rounded">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            <span className="text-blue-400 text-xs">{updateMessage}</span>
          </div>
        )}

        {/* Success message after update */}
        {!isUpdating && updateMessage && (
          <div className="flex items-center gap-2 px-3 py-1 bg-green-900/30 border border-green-700/50 rounded">
            <span className="text-green-400 text-xs">{updateMessage}</span>
          </div>
        )}

        {/* Last B3 update date */}
        <div className="flex items-center gap-2 px-3 py-1 bg-dark-bg rounded border border-dark-border">
          <Database className="w-3.5 h-3.5 text-dark-muted" />
          <span className="text-dark-muted text-xs">B3:</span>
          <span className="text-dark-text text-xs font-medium">
            {lastB3Date ? formatDate(lastB3Date) : '--/--/----'}
          </span>
        </div>

        <button className="p-2 hover:bg-dark-border rounded">
          <Bell className="w-4 h-4 text-dark-muted" />
        </button>

        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          title={isDark ? 'Modo claro' : 'Modo escuro'}
          className="p-2 hover:bg-dark-border rounded transition-colors"
        >
          {isDark
            ? <Sun className="w-4 h-4 text-dark-muted hover:text-dark-text" />
            : <Moon className="w-4 h-4 text-dark-muted hover:text-dark-text" />
          }
        </button>

        <button className="p-2 hover:bg-dark-border rounded">
          <Settings className="w-4 h-4 text-dark-muted" />
        </button>
      </div>
    </div>
  )
}
