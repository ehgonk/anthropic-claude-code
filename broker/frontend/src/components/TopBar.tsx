import { Menu, Settings, Bell, Database } from 'lucide-react'
import ThemeSwitcher, { ThemeMode } from './ThemeSwitcher'
import LayoutPicker, { GridLayout } from './LayoutPicker'

interface TopBarProps {
  lastUpdateDate: string | null
  isUpdating: boolean
  updateMessage: string | null
  themeMode: ThemeMode
  onThemeChange: (theme: ThemeMode) => void
  layout: GridLayout
  onSelectLayout: (layout: GridLayout) => void
}

export default function TopBar({ lastUpdateDate, isUpdating, updateMessage, themeMode, onThemeChange, layout, onSelectLayout }: TopBarProps) {
  return (
    <div className="h-12 bg-dark-card border-b border-dark-border flex items-center justify-between px-4">
      <div className="flex items-center gap-4">
        <button className="p-1 hover:bg-dark-border rounded">
          <Menu className="w-5 h-5 text-dark-muted" />
        </button>

        <span className="text-lg font-bold text-dark-text">Dojima</span>

        <div className="ml-4 pl-4 border-l border-dark-border">
          <LayoutPicker layout={layout} onSelect={onSelectLayout} />
        </div>
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

        {/* Last update date (already formatted as dd/mm/yyyy from backend) */}
        <div className="flex items-center gap-2 px-3 py-1 bg-dark-bg rounded border border-dark-border">
          <Database className="w-3.5 h-3.5 text-dark-muted" />
          <span className="text-dark-muted text-xs">Última atualização:</span>
          <span className="text-dark-text text-xs font-medium">
            {lastUpdateDate || '--/--/----'}
          </span>
        </div>

        <button className="p-2 hover:bg-dark-border rounded">
          <Bell className="w-4 h-4 text-dark-muted" />
        </button>

        <ThemeSwitcher currentTheme={themeMode} onThemeChange={onThemeChange} />

        <button className="p-2 hover:bg-dark-border rounded">
          <Settings className="w-4 h-4 text-dark-muted" />
        </button>
      </div>
    </div>
  )
}
