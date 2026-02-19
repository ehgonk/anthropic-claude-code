import { Star, Plus, X, TrendingUp, TrendingDown } from 'lucide-react'
import type { Stock } from '../App'

interface WatchlistPanelProps {
  watchlist: Stock[]
  allStocks: Stock[]
  onAddToWatchlist: (stock: Stock) => void
  onRemoveFromWatchlist: (symbol: string) => void
  onSelectStock: (stock: Stock) => void
}

export default function WatchlistPanel({
  watchlist,
  allStocks,
  onAddToWatchlist,
  onRemoveFromWatchlist,
  onSelectStock
}: WatchlistPanelProps) {
  const availableStocks = allStocks.filter(
    stock => !watchlist.find(w => w.symbol === stock.symbol)
  )

  return (
    <div className="w-64 bg-dark-card border-r border-dark-border flex flex-col">
      <div className="px-4 py-3 border-b border-dark-border">
        <h3 className="text-sm font-semibold text-dark-text flex items-center gap-2">
          <Star className="w-4 h-4 text-yellow-500" />
          Watchlist
        </h3>
        <p className="text-xs text-dark-muted mt-1">
          Suas ações favoritas
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Watchlist Items */}
        {watchlist.length > 0 ? (
          <div className="p-2 space-y-1">
            {watchlist.map((stock) => (
              <div
                key={stock.symbol}
                className="group relative bg-dark-border/30 hover:bg-dark-border rounded p-2 transition-colors"
              >
                <button
                  onClick={() => onSelectStock(stock)}
                  className="w-full text-left"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold text-dark-text">{stock.symbol}</span>
                    <span className="text-xs text-dark-muted">
                      R$ {stock.price.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-dark-muted truncate flex-1 pr-2">
                      {stock.name}
                    </span>
                    <span className={`text-xs font-medium flex items-center gap-0.5 ${
                      stock.change_percent >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {stock.change_percent >= 0 ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      {Math.abs(stock.change_percent).toFixed(2)}%
                    </span>
                  </div>
                </button>
                <button
                  onClick={() => onRemoveFromWatchlist(stock.symbol)}
                  className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 p-1 bg-dark-bg rounded hover:bg-red-600/20 transition-all"
                  title="Remover da watchlist"
                >
                  <X className="w-3 h-3 text-red-400" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 text-center text-dark-muted text-sm">
            <Star className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p>Sua watchlist está vazia</p>
            <p className="text-xs mt-1">Adicione ações abaixo</p>
          </div>
        )}

        {/* Add Stocks Section */}
        {availableStocks.length > 0 && (
          <div className="border-t border-dark-border mt-2">
            <div className="px-4 py-2 bg-dark-bg/50">
              <h4 className="text-xs font-semibold text-dark-muted uppercase flex items-center gap-1">
                <Plus className="w-3 h-3" />
                Adicionar Ações
              </h4>
            </div>
            <div className="p-2 space-y-1 max-h-48 overflow-y-auto">
              {availableStocks.map((stock) => (
                <button
                  key={stock.symbol}
                  onClick={() => onAddToWatchlist(stock)}
                  className="w-full text-left px-2 py-1.5 rounded hover:bg-dark-border transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-dark-text">{stock.symbol}</span>
                    <Plus className="w-3 h-3 text-dark-muted" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="px-4 py-3 border-t border-dark-border">
        <div className="text-xs text-dark-muted">
          {watchlist.length} ação{watchlist.length !== 1 ? 'ões' : ''} na watchlist
        </div>
      </div>
    </div>
  )
}
