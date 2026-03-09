import { useState } from 'react'
import { Search, ChevronRight, ChevronUp, ChevronDown, X } from 'lucide-react'
import type { Stock } from '../App'

interface StockListProps {
  stocks: Stock[]
  selectedStock: Stock | null
  onStockSelect: (stock: Stock) => void
}

type SortField = 'symbol' | 'price' | 'change_percent' | 'volume'
type SortDir = 'asc' | 'desc'

function formatVolume(num: number) {
  if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(2)}B`
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(2)}M`
  if (num >= 1_000) return `${(num / 1_000).toFixed(2)}K`
  return num.toFixed(0)
}

export default function StockList({ stocks, selectedStock, onStockSelect }: StockListProps) {
  const [query, setQuery] = useState('')
  const [sortField, setSortField] = useState<SortField>('volume')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [collapsed, setCollapsed] = useState(false)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir(field === 'symbol' ? 'asc' : 'desc')
    }
  }

  const filtered = stocks.filter(s =>
    s.symbol.toLowerCase().includes(query.toLowerCase()) ||
    s.name.toLowerCase().includes(query.toLowerCase())
  )

  const sorted = [...filtered].sort((a, b) => {
    let cmp = 0
    if (sortField === 'symbol') cmp = a.symbol.localeCompare(b.symbol)
    else if (sortField === 'price') cmp = a.price - b.price
    else if (sortField === 'change_percent') cmp = a.change_percent - b.change_percent
    else cmp = a.volume - b.volume
    return sortDir === 'asc' ? cmp : -cmp
  })

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ChevronDown className="w-3 h-3 opacity-20" />
    return sortDir === 'asc'
      ? <ChevronUp className="w-3 h-3 opacity-70" />
      : <ChevronDown className="w-3 h-3 opacity-70" />
  }

  if (collapsed) {
    return (
      <div
        className="w-6 bg-dark-card border-l border-dark-border flex items-center justify-center cursor-pointer hover:bg-dark-border/30 transition-colors"
        onClick={() => setCollapsed(false)}
        title="Expandir lista"
      >
        <ChevronRight className="w-4 h-4 text-dark-muted" />
      </div>
    )
  }

  const ColHeader = ({ field, label, className = '' }: { field: SortField; label: string; className?: string }) => (
    <button
      onClick={() => handleSort(field)}
      className={`flex items-center gap-0.5 hover:text-dark-text transition-colors ${className}`}
    >
      {label}
      <SortIcon field={field} />
    </button>
  )

  return (
    <div className="w-80 bg-dark-card border-l border-dark-border flex flex-col">
      {/* Search bar with collapse button */}
      <div className="p-3 border-b border-dark-border flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted" />
          <input
            type="text"
            placeholder="Pesquisar símbolo"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="w-full pl-10 pr-8 py-2 bg-dark-bg border border-dark-border rounded text-sm text-dark-text placeholder-dark-muted focus:outline-none focus:border-dark-muted"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-dark-muted hover:text-dark-text transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        <button
          onClick={() => setCollapsed(true)}
          title="Retrair lista"
          className="p-1.5 hover:bg-dark-border rounded text-dark-muted hover:text-dark-text transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-12 gap-1 px-3 py-2 text-xs text-dark-muted border-b border-dark-border select-none">
        <div className="col-span-4">
          <ColHeader field="symbol" label="Símbolo" />
        </div>
        <div className="col-span-3 flex justify-center">
          <ColHeader field="price" label="Preço" />
        </div>
        <div className="col-span-2 flex justify-center">
          <ColHeader field="change_percent" label="%" />
        </div>
        <div className="col-span-3 flex justify-end">
          <ColHeader field="volume" label="Volume" />
        </div>
      </div>

      {/* Stock list */}
      <div className="flex-1 overflow-y-auto">
        {sorted.map((stock) => {
          const isSelected = selectedStock?.symbol === stock.symbol
          const isPositive = stock.change_percent >= 0

          return (
            <div
              key={stock.symbol}
              onClick={() => onStockSelect(stock)}
              className={`grid grid-cols-12 gap-1 px-3 py-2.5 cursor-pointer transition-colors border-b border-dark-border/50 ${
                isSelected ? 'bg-dark-border/50' : 'hover:bg-dark-border/30'
              }`}
            >
              <div className="col-span-4 flex flex-col min-w-0">
                <span className="text-dark-text text-sm font-medium leading-tight">{stock.symbol}</span>
                <span className="text-dark-muted text-xs truncate leading-tight min-h-[1rem]">{stock.name}</span>
              </div>

              <div className="col-span-3 flex items-center justify-center">
                <span className="text-dark-text text-sm">
                  R$ {stock.price.toFixed(2)}
                </span>
              </div>

              <div className="col-span-2 flex items-center justify-center">
                <span className={`text-xs font-medium ${isPositive ? 'text-green-profit' : 'text-red-loss'}`}>
                  {isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%
                </span>
              </div>

              <div className="col-span-3 flex items-center justify-end">
                <span className="text-dark-muted text-xs">
                  {formatVolume(stock.volume)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
