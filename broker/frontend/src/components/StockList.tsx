import { Search } from 'lucide-react'
import type { Stock } from '../App'

interface StockListProps {
  stocks: Stock[]
  selectedStock: Stock | null
  onStockSelect: (stock: Stock) => void
}

export default function StockList({ stocks, selectedStock, onStockSelect }: StockListProps) {
  const formatNumber = (num: number) => {
    if (num >= 1000000000) {
      return `${(num / 1000000000).toFixed(2)}B`
    }
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(2)}M`
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(2)}K`
    }
    return num.toFixed(2)
  }

  return (
    <div className="w-80 bg-dark-card border-l border-dark-border flex flex-col">
      {/* Search bar */}
      <div className="p-3 border-b border-dark-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted" />
          <input
            type="text"
            placeholder="Search symbols..."
            className="w-full pl-10 pr-3 py-2 bg-dark-bg border border-dark-border rounded text-sm text-white placeholder-dark-muted focus:outline-none focus:border-dark-text"
          />
        </div>
      </div>

      {/* Stock list header */}
      <div className="grid grid-cols-12 gap-2 px-3 py-2 text-xs text-dark-muted border-b border-dark-border">
        <div className="col-span-4">Symbol</div>
        <div className="col-span-3 text-right">Price</div>
        <div className="col-span-2 text-right">%</div>
        <div className="col-span-3 text-right">Volume</div>
      </div>

      {/* Stock list */}
      <div className="flex-1 overflow-y-auto">
        {stocks.map((stock) => {
          const isSelected = selectedStock?.symbol === stock.symbol
          const isPositive = stock.change_percent >= 0

          return (
            <div
              key={stock.symbol}
              onClick={() => onStockSelect(stock)}
              className={`grid grid-cols-12 gap-2 px-3 py-3 cursor-pointer transition-colors border-b border-dark-border/50 ${
                isSelected
                  ? 'bg-dark-border/50'
                  : 'hover:bg-dark-border/30'
              }`}
            >
              <div className="col-span-4 flex flex-col">
                <span className="text-white text-sm font-medium">{stock.symbol}</span>
                <span className="text-dark-muted text-xs truncate">{stock.name}</span>
              </div>

              <div className="col-span-3 text-right">
                <span className="text-white text-sm">
                  R$ {stock.price.toFixed(2)}
                </span>
              </div>

              <div className="col-span-2 text-right">
                <span className={`text-sm font-medium ${
                  isPositive ? 'text-green-profit' : 'text-red-loss'
                }`}>
                  {isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%
                </span>
              </div>

              <div className="col-span-3 text-right">
                <span className="text-dark-muted text-xs">
                  {formatNumber(stock.volume)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
