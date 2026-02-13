import { useState, useEffect } from 'react'
import Chart from './components/Chart'
import StockList from './components/StockList'
import TopBar from './components/TopBar'
import LeftBar from './components/LeftBar'
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

function App() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null)
  const [candleData, setCandleData] = useState<CandleData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStocks()
  }, [])

  useEffect(() => {
    if (selectedStock) {
      loadCandleData(selectedStock.symbol)
    }
  }, [selectedStock])

  const loadStocks = async () => {
    try {
      const data = await api.getStocks()
      setStocks(data)
      if (data.length > 0 && !selectedStock) {
        setSelectedStock(data[0])
      }
    } catch (error) {
      console.error('Error loading stocks:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCandleData = async (symbol: string) => {
    try {
      const data = await api.getCandleData(symbol)
      setCandleData(data)
    } catch (error) {
      console.error('Error loading candle data:', error)
    }
  }

  const handleStockSelect = (stock: Stock) => {
    setSelectedStock(stock)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-bg">
        <div className="text-dark-muted">Loading...</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-dark-bg">
      <TopBar selectedStock={selectedStock} />

      <div className="flex flex-1 overflow-hidden">
        <LeftBar />

        <div className="flex-1 flex flex-col">
          <Chart
            data={candleData}
            selectedStock={selectedStock}
          />
        </div>

        <StockList
          stocks={stocks}
          selectedStock={selectedStock}
          onStockSelect={handleStockSelect}
        />
      </div>
    </div>
  )
}

export default App
