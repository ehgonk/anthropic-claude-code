import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, HistogramData } from 'lightweight-charts'
import type { Stock, CandleData } from '../App'

export type ChartPeriod = '1D' | '1W' | '1M' | '3M' | '1Y'

interface ChartProps {
  data: CandleData[]
  selectedStock: Stock | null
  isDark?: boolean
}

/**
 * Aggregate daily candles into a higher timeframe.
 *
 * Rules (TradingView standard):
 * - Open  = first candle's open in the period
 * - High  = max high across all candles in the period
 * - Low   = min low across all candles in the period
 * - Close = last candle's close in the period
 * - Volume = sum of all volumes in the period
 */
function aggregateCandles(dailyData: CandleData[], period: ChartPeriod): CandleData[] {
  if (period === '1D' || dailyData.length === 0) return dailyData

  const getGroupKey = (dateStr: string): string => {
    const d = new Date(dateStr + 'T00:00:00')
    const year = d.getFullYear()
    const month = d.getMonth() // 0-based

    switch (period) {
      case '1W': {
        // ISO week: Monday-start week
        // Get the Monday of this week
        const day = d.getDay() // 0=Sun, 1=Mon, ..., 6=Sat
        const diff = day === 0 ? -6 : 1 - day // offset to Monday
        const monday = new Date(d)
        monday.setDate(d.getDate() + diff)
        return monday.toISOString().slice(0, 10)
      }
      case '1M': {
        // Monthly: group by YYYY-MM
        return `${year}-${String(month + 1).padStart(2, '0')}`
      }
      case '3M': {
        // Quarterly: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec
        const quarter = Math.floor(month / 3) + 1
        return `${year}-Q${quarter}`
      }
      case '1Y': {
        // Yearly: group by year
        return `${year}`
      }
      default:
        return dateStr
    }
  }

  // Group candles by period key, maintaining order
  const groups: Map<string, CandleData[]> = new Map()
  for (const candle of dailyData) {
    const key = getGroupKey(candle.time)
    if (!groups.has(key)) {
      groups.set(key, [])
    }
    groups.get(key)!.push(candle)
  }

  // Aggregate each group
  const result: CandleData[] = []
  for (const [, candles] of groups) {
    if (candles.length === 0) continue

    // Use the first trading day's date as the candle timestamp
    const firstCandle = candles[0]
    const lastCandle = candles[candles.length - 1]

    result.push({
      time: firstCandle.time,
      open: firstCandle.open,
      high: Math.max(...candles.map(c => c.high)),
      low: Math.min(...candles.map(c => c.low)),
      close: lastCandle.close,
      volume: candles.reduce((sum, c) => sum + c.volume, 0),
    })
  }

  return result
}

const darkChartTheme = {
  background: '#131722',
  text: '#d1d4dc',
  grid: '#1e222d',
  border: '#2a2e39',
  crosshair: '#758696',
  crosshairLabel: '#4c525e',
}

const lightChartTheme = {
  background: '#ffffff',
  text: '#131722',
  grid: '#f0f0f0',
  border: '#e1e1e1',
  crosshair: '#9b9ea3',
  crosshairLabel: '#dde1ed',
}

export default function Chart({ data, selectedStock, isDark = true }: ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const [period, setPeriod] = useState<ChartPeriod>('1D')

  useEffect(() => {
    if (!chartContainerRef.current) return

    const theme = isDark ? darkChartTheme : lightChartTheme
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: theme.background },
        textColor: theme.text,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: theme.grid },
        horzLines: { color: theme.grid },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: theme.border,
      },
      rightPriceScale: {
        borderColor: theme.border,
      },
      crosshair: {
        horzLine: {
          color: theme.crosshair,
          labelBackgroundColor: theme.crosshairLabel,
        },
        vertLine: {
          color: theme.crosshair,
          labelBackgroundColor: theme.crosshairLabel,
        },
      },
    })

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    })

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.7,
        bottom: 0,
      },
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries
    volumeSeriesRef.current = volumeSeries

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  // Update chart colors when theme changes
  useEffect(() => {
    if (!chartRef.current) return
    const theme = isDark ? darkChartTheme : lightChartTheme
    chartRef.current.applyOptions({
      layout: {
        background: { color: theme.background },
        textColor: theme.text,
      },
      grid: {
        vertLines: { color: theme.grid },
        horzLines: { color: theme.grid },
      },
      timeScale: { borderColor: theme.border },
      rightPriceScale: { borderColor: theme.border },
      crosshair: {
        horzLine: { color: theme.crosshair, labelBackgroundColor: theme.crosshairLabel },
        vertLine: { color: theme.crosshair, labelBackgroundColor: theme.crosshairLabel },
      },
    })
  }, [isDark])

  // Re-render chart data when data or period changes
  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || data.length === 0) return

    const aggregated = aggregateCandles(data, period)

    const candleData: CandlestickData[] = aggregated.map((d) => ({
      time: d.time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }))

    const volumeData: HistogramData[] = aggregated.map((d) => ({
      time: d.time,
      value: d.volume,
      color: d.close >= d.open ? '#26a69a80' : '#ef535080',
    }))

    candlestickSeriesRef.current.setData(candleData)
    volumeSeriesRef.current.setData(volumeData)

    if (chartRef.current) {
      chartRef.current.timeScale().fitContent()
    }
  }, [data, period])

  const periods: ChartPeriod[] = ['1D', '1W', '1M', '3M', '1Y']

  const periodLabels: Record<ChartPeriod, string> = {
    '1D': 'Diário',
    '1W': 'Semanal',
    '1M': 'Mensal',
    '3M': 'Trimestral',
    '1Y': 'Anual',
  }

  return (
    <div className="flex-1 flex flex-col bg-dark-card">
      {/* Chart header */}
      <div className="flex items-center gap-4 px-4 py-2 border-b border-dark-border">
        <div className="flex items-center gap-2">
          <span className="text-dark-text font-semibold text-lg">
            {selectedStock?.symbol || 'Select a stock'}
          </span>
          {selectedStock && (
            <>
              <span className="text-dark-muted text-sm">{selectedStock.name}</span>
              <span className={`text-sm font-semibold ${
                selectedStock.change_percent >= 0 ? 'text-green-profit' : 'text-red-loss'
              }`}>
                {selectedStock.change_percent >= 0 ? '+' : ''}
                {selectedStock.change_percent.toFixed(2)}%
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-1 ml-auto">
          {periods.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              title={periodLabels[p]}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                period === p
                  ? 'text-dark-text bg-dark-border'
                  : 'text-dark-muted hover:text-dark-text hover:bg-dark-border/50'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Chart container */}
      <div ref={chartContainerRef} className="flex-1" />
    </div>
  )
}
