import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, HistogramData, LineData } from 'lightweight-charts'
import type { Stock, CandleData } from '../App'
import { calculateSMA, calculateEMA } from '../utils/indicators'

export type ChartPeriod = '1D' | '1W' | '1M' | '3M' | '1Y'

interface ChartProps {
  data: CandleData[]
  selectedStock: Stock | null
  isDark?: boolean
  activeIndicators?: string[]
}

function aggregateCandles(dailyData: CandleData[], period: ChartPeriod): CandleData[] {
  if (period === '1D' || dailyData.length === 0) return dailyData

  const getGroupKey = (dateStr: string): string => {
    const d = new Date(dateStr + 'T00:00:00')
    const year = d.getFullYear()
    const month = d.getMonth()

    switch (period) {
      case '1W': {
        const day = d.getDay()
        const diff = day === 0 ? -6 : 1 - day
        const monday = new Date(d)
        monday.setDate(d.getDate() + diff)
        return monday.toISOString().slice(0, 10)
      }
      case '1M':
        return `${year}-${String(month + 1).padStart(2, '0')}`
      case '3M': {
        const quarter = Math.floor(month / 3) + 1
        return `${year}-Q${quarter}`
      }
      case '1Y':
        return `${year}`
      default:
        return dateStr
    }
  }

  const groups: Map<string, CandleData[]> = new Map()
  for (const candle of dailyData) {
    const key = getGroupKey(candle.time)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(candle)
  }

  const result: CandleData[] = []
  for (const [, candles] of groups) {
    if (candles.length === 0) continue
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

export default function Chart({ data, selectedStock, isDark = false, activeIndicators = [] }: ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const indicatorSeriesRef = useRef<Map<string, ISeriesApi<'Line'>>>(new Map())
  const [period, setPeriod] = useState<ChartPeriod>('1D')
  const [chartReady, setChartReady] = useState(false)

  // Create chart once container is mounted
  useEffect(() => {
    const container = chartContainerRef.current
    if (!container) return

    const theme = isDark ? darkChartTheme : lightChartTheme

    const chart = createChart(container, {
      width: container.clientWidth || 300,
      height: container.clientHeight || 300,
      layout: {
        background: { color: theme.background },
        textColor: theme.text,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: theme.grid },
        horzLines: { color: theme.grid },
      },
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
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    })

    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.7, bottom: 0 },
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries
    volumeSeriesRef.current = volumeSeries
    setChartReady(true)

    // Manual resize observer for reliable sizing
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        if (width > 0 && height > 0) {
          chart.applyOptions({ width, height })
        }
      }
    })
    ro.observe(container)

    return () => {
      ro.disconnect()
      chart.remove()
      chartRef.current = null
      candlestickSeriesRef.current = null
      volumeSeriesRef.current = null
      setChartReady(false)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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

  // Apply data when chart is ready and data changes
  useEffect(() => {
    if (!chartReady || !candlestickSeriesRef.current || !volumeSeriesRef.current || data.length === 0) return

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
  }, [data, period, chartReady])

  // Update indicators when activeIndicators or data changes
  useEffect(() => {
    if (!chartReady || !chartRef.current || data.length === 0) return

    const chart = chartRef.current
    const aggregated = aggregateCandles(data, period)

    // Define indicator colors and configurations
    const indicatorConfig: Record<string, { color: string; calculate: () => LineData[] }> = {
      sma20: {
        color: '#2962FF',
        calculate: () => calculateSMA(aggregated, 20).map(d => ({ time: d.time, value: d.value })),
      },
      sma50: {
        color: '#FF6D00',
        calculate: () => calculateSMA(aggregated, 50).map(d => ({ time: d.time, value: d.value })),
      },
      sma200: {
        color: '#E91E63',
        calculate: () => calculateSMA(aggregated, 200).map(d => ({ time: d.time, value: d.value })),
      },
      ema9: {
        color: '#00BCD4',
        calculate: () => calculateEMA(aggregated, 9).map(d => ({ time: d.time, value: d.value })),
      },
      ema21: {
        color: '#9C27B0',
        calculate: () => calculateEMA(aggregated, 21).map(d => ({ time: d.time, value: d.value })),
      },
    }

    // Remove indicators that are no longer active
    const currentSeries = indicatorSeriesRef.current
    for (const [id, series] of currentSeries.entries()) {
      if (!activeIndicators.includes(id)) {
        chart.removeSeries(series)
        currentSeries.delete(id)
      }
    }

    // Add or update active indicators
    for (const indicatorId of activeIndicators) {
      const config = indicatorConfig[indicatorId]
      if (!config) continue

      try {
        const indicatorData = config.calculate()

        if (!currentSeries.has(indicatorId)) {
          // Create new series
          const lineSeries = chart.addLineSeries({
            color: config.color,
            lineWidth: 2,
            crosshairMarkerVisible: true,
            lastValueVisible: true,
            priceLineVisible: false,
          })
          lineSeries.setData(indicatorData)
          currentSeries.set(indicatorId, lineSeries)
        } else {
          // Update existing series
          const series = currentSeries.get(indicatorId)!
          series.setData(indicatorData)
        }
      } catch (error) {
        console.warn(`Error calculating indicator ${indicatorId}:`, error)
      }
    }
  }, [chartReady, data, period, activeIndicators])

  const periods: ChartPeriod[] = ['1D', '1W', '1M', '3M', '1Y']

  const periodLabels: Record<ChartPeriod, string> = {
    '1D': 'Diário',
    '1W': 'Semanal',
    '1M': 'Mensal',
    '3M': 'Trimestral',
    '1Y': 'Anual',
  }

  return (
    <div className="h-full flex flex-col bg-dark-card overflow-hidden">
      {/* Chart header */}
      <div className="flex items-center gap-4 px-4 py-2 border-b border-dark-border shrink-0">
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

      {/* Chart container - uses absolute fill for reliable dimensions */}
      <div className="flex-1 relative min-h-0">
        <div ref={chartContainerRef} className="absolute inset-0" />
      </div>
    </div>
  )
}
