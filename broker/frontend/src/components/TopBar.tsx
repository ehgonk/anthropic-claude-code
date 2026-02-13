import { Menu, Settings, Bell } from 'lucide-react'
import type { Stock } from '../App'

interface TopBarProps {
  selectedStock: Stock | null
}

export default function TopBar({ selectedStock }: TopBarProps) {
  return (
    <div className="h-12 bg-dark-card border-b border-dark-border flex items-center justify-between px-4">
      <div className="flex items-center gap-4">
        <button className="p-1 hover:bg-dark-border rounded">
          <Menu className="w-5 h-5 text-dark-muted" />
        </button>

        <span className="text-lg font-bold text-white">Broker</span>

        {selectedStock && (
          <div className="flex items-center gap-3 ml-4 pl-4 border-l border-dark-border">
            <div className="flex items-center gap-2">
              <span className="text-white font-semibold">{selectedStock.symbol}</span>
              <span className="text-xl font-bold text-white">
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

      <div className="flex items-center gap-2">
        <button className="p-2 hover:bg-dark-border rounded">
          <Bell className="w-4 h-4 text-dark-muted" />
        </button>
        <button className="p-2 hover:bg-dark-border rounded">
          <Settings className="w-4 h-4 text-dark-muted" />
        </button>
      </div>
    </div>
  )
}
