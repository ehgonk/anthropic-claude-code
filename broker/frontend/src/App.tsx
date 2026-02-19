import { useState, useEffect, useCallback } from 'react'
import Chart from './components/Chart'
import StockList from './components/StockList'
import TopBar from './components/TopBar'
import LeftBar from './components/LeftBar'
import IndicatorsPanel from './components/IndicatorsPanel'
import TrendsPanel from './components/TrendsPanel'
import BarsPanel from './components/BarsPanel'
import LinesPanel from './components/LinesPanel'
import WatchlistPanel from './components/WatchlistPanel'
import LayersPanel from './components/LayersPanel'
import LayoutPicker, { GridLayout, LAYOUTS } from './components/LayoutPicker'
import api from './services/api'

export interface Stock {
  symbol: string
  name: string
  price: number
  change_percent: number
  volume: number
}

export interface CandleData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

const MAX_PANELS = 16

interface ChartPanel {
  stock: Stock | null
  candleData: CandleData[]
}

function makeEmptyPanels(): ChartPanel[] {
  return Array.from({ length: MAX_PANELS }, () => ({ stock: null, candleData: [] }))
}

function App() {
  const [isDark, setIsDark] = useState(true)
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(true)
  const [lastB3Date, setLastB3Date] = useState<string | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const [updateMessage, setUpdateMessage] = useState<string | null>(null)
  const [layout, setLayout] = useState<GridLayout>(LAYOUTS[0]) // 1x1 default
  const [panels, setPanels] = useState<ChartPanel[]>(makeEmptyPanels())
  const [activePanel, setActivePanel] = useState(0)
  const [activeTool, setActiveTool] = useState<string | null>(null)
  const [activeIndicators, setActiveIndicators] = useState<string[]>([])
  const [activeTrends, setActiveTrends] = useState<string[]>([])
  const [selectedTimeframe, setSelectedTimeframe] = useState('1d')
  const [selectedCandleType, setSelectedCandleType] = useState('candlestick')
  const [activeDrawingTool, setActiveDrawingTool] = useState<string | null>(null)
  const [watchlist, setWatchlist] = useState<Stock[]>([])
  const [visibleLayers, setVisibleLayers] = useState<string[]>(['volume', 'grid', 'price-labels', 'time-labels', 'last-price'])

  const loadCandleData = useCallback(async (symbol: string, panelIndex: number) => {
    try {
      const data = await api.getCandleData(symbol)
      setPanels(prev => {
        const updated = [...prev]
        updated[panelIndex] = { ...updated[panelIndex], candleData: data }
        return updated
      })
    } catch (error) {
      console.error('Error loading candle data:', error)
    }
  }, [])

  // Auto-update on startup
  useEffect(() => {
    const initializeApp = async () => {
      try {
        const stocksData = await api.getStocks()
        setStocks(stocksData)

        if (stocksData.length > 0) {
          setPanels(prev => {
            const updated = [...prev]
            updated[0] = { ...updated[0], stock: stocksData[0] }
            if (stocksData.length > 1) updated[1] = { ...updated[1], stock: stocksData[1] }
            if (stocksData.length > 2) updated[2] = { ...updated[2], stock: stocksData[2] }
            return updated
          })
        }

        const lastUpdate = await api.getLastUpdate()
        setLastB3Date(lastUpdate.last_date)
        setLoading(false)

        setIsUpdating(true)
        setUpdateMessage('Atualizando histórico de cotações B3...')

        const currentYear = new Date().getFullYear()
        try {
          const result = await api.ingestB3(currentYear)
          setUpdateMessage(`Atualizado: ${result.price_records} registros de ${result.stocks_processed} ações`)

          const updatedStocks = await api.getStocks()
          setStocks(updatedStocks)

          const updatedLastUpdate = await api.getLastUpdate()
          setLastB3Date(updatedLastUpdate.last_date)

          if (updatedStocks.length > 0) {
            setPanels(prev => prev.map((panel) => {
              if (!panel.stock) return panel
              const updated = updatedStocks.find(s => s.symbol === panel.stock!.symbol)
              return updated ? { ...panel, stock: updated } : panel
            }))
          }
        } catch {
          setUpdateMessage(lastUpdate.last_date
            ? `Usando dados de ${lastUpdate.last_date}`
            : 'Dados B3 carregados do cache local')
        }
      } catch (error) {
        console.error('Error initializing app:', error)
        setLoading(false)
        setUpdateMessage('Erro ao conectar com o backend')
      } finally {
        setIsUpdating(false)
        setTimeout(() => setUpdateMessage(null), 5000)
      }
    }

    initializeApp()
  }, [])

  // Load candle data when panel stocks change
  useEffect(() => {
    panels.forEach((panel, index) => {
      if (panel.stock && panel.candleData.length === 0) {
        loadCandleData(panel.stock.symbol, index)
      }
    })
  }, [panels, loadCandleData])

  const handleStockSelect = (stock: Stock) => {
    setPanels(prev => {
      const updated = [...prev]
      updated[activePanel] = { stock, candleData: [] }
      return updated
    })
    loadCandleData(stock.symbol, activePanel)
  }

  const toggleTheme = () => {
    setIsDark(prev => {
      const next = !prev
      document.documentElement.classList.toggle('dark', next)
      return next
    })
  }

  const toggleIndicator = (indicatorId: string) => {
    setActiveIndicators(prev =>
      prev.includes(indicatorId)
        ? prev.filter(id => id !== indicatorId)
        : [...prev, indicatorId]
    )
  }

  const toggleTrend = (trendId: string) => {
    setActiveTrends(prev =>
      prev.includes(trendId)
        ? prev.filter(id => id !== trendId)
        : [...prev, trendId]
    )
  }

  const handleAddToWatchlist = (stock: Stock) => {
    setWatchlist(prev => [...prev, stock])
  }

  const handleRemoveFromWatchlist = (symbol: string) => {
    setWatchlist(prev => prev.filter(s => s.symbol !== symbol))
  }

  const toggleLayer = (layerId: string) => {
    setVisibleLayers(prev =>
      prev.includes(layerId)
        ? prev.filter(id => id !== layerId)
        : [...prev, layerId]
    )
  }

  // Apply dark class on mount
  useEffect(() => {
    document.documentElement.classList.add('dark')
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-bg">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          <div className="text-dark-muted text-sm">Carregando dados...</div>
        </div>
      </div>
    )
  }

  const totalPanels = layout.cols * layout.rows

  return (
    <div className="flex flex-col h-screen bg-dark-bg">
      <TopBar
        selectedStock={panels[activePanel].stock}
        lastB3Date={lastB3Date}
        isUpdating={isUpdating}
        updateMessage={updateMessage}
        isDark={isDark}
        onToggleTheme={toggleTheme}
      />

      <div className="flex flex-1 overflow-hidden">
        <LeftBar
          activeTool={activeTool}
          onToolSelect={(tool) => {
            console.log('📊 App: onToolSelect called with:', tool)
            console.log('📊 App: current activeTool:', activeTool)
            const newTool = activeTool === tool ? null : tool
            console.log('📊 App: setting activeTool to:', newTool)
            setActiveTool(newTool)
            console.log('📊 App: activeTool updated to:', newTool)
          }}
        />

        {/* DEBUG INDICATOR */}
        {activeTool && (
          <div className="fixed top-20 left-20 bg-red-500 text-white px-4 py-2 rounded z-50">
            Active Tool: {activeTool}
          </div>
        )}

        {activeTool === 'trends' && (
          <TrendsPanel
            activeTrends={activeTrends}
            onToggleTrend={toggleTrend}
          />
        )}

        {activeTool === 'bars' && (
          <BarsPanel
            selectedTimeframe={selectedTimeframe}
            selectedCandleType={selectedCandleType}
            onTimeframeChange={setSelectedTimeframe}
            onCandleTypeChange={setSelectedCandleType}
          />
        )}

        {activeTool === 'lines' && (
          <LinesPanel
            activeTool={activeDrawingTool}
            onToolSelect={(tool) => setActiveDrawingTool(activeDrawingTool === tool ? null : tool)}
            onClearAll={() => console.log('Clear all drawings')}
          />
        )}

        {activeTool === 'indicators' && (
          <IndicatorsPanel
            activeIndicators={activeIndicators}
            onToggleIndicator={toggleIndicator}
          />
        )}

        {activeTool === 'watchlist' && (
          <WatchlistPanel
            watchlist={watchlist}
            allStocks={stocks}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
            onSelectStock={handleStockSelect}
          />
        )}

        {activeTool === 'layers' && (
          <LayersPanel
            visibleLayers={visibleLayers}
            onToggleLayer={toggleLayer}
          />
        )}

        <div className="flex-1 flex flex-col min-w-0">
          {/* Layout control bar */}
          <div className="flex items-center justify-between px-4 py-1 bg-dark-card border-b border-dark-border">
            <div className="flex items-center gap-1 flex-wrap">
              {totalPanels > 1 && Array.from({ length: totalPanels }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setActivePanel(i)}
                  className={`px-2 py-0.5 text-xs rounded transition-colors ${
                    activePanel === i
                      ? 'text-white bg-blue-600'
                      : 'text-dark-muted hover:text-dark-text bg-dark-border/50'
                  }`}
                >
                  {panels[i].stock?.symbol || `T${i + 1}`}
                </button>
              ))}
            </div>
            <LayoutPicker layout={layout} onSelect={(l) => {
              setLayout(l)
              // keep activePanel within bounds
              if (activePanel >= l.cols * l.rows) setActivePanel(0)
            }} />
          </div>

          {/* Chart panels */}
          <div
            className="flex-1 gap-px bg-dark-border"
            style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${layout.cols}, 1fr)`,
              gridTemplateRows: `repeat(${layout.rows}, 1fr)`,
            }}
          >
            {Array.from({ length: totalPanels }).map((_, i) => (
              <div
                key={i}
                onClick={() => setActivePanel(i)}
                className={`relative min-w-0 min-h-0 overflow-hidden ${activePanel === i && totalPanels > 1 ? 'ring-1 ring-inset ring-blue-500/50' : ''}`}
              >
                <Chart
                  data={panels[i].candleData}
                  selectedStock={panels[i].stock}
                  isDark={isDark}
                  activeIndicators={activeIndicators}
                />
              </div>
            ))}
          </div>
        </div>

        <StockList
          stocks={stocks}
          selectedStock={panels[activePanel].stock}
          onStockSelect={handleStockSelect}
        />
      </div>
    </div>
  )
}

export default App
