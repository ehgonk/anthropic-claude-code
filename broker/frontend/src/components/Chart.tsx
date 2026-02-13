import { useEffect, useRef } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, HistogramData } from 'lightweight-charts'
import type { Stock, CandleData } from '../App'

interface ChartProps {
  data: CandleData[]
  selectedStock: Stock | null
}

export default function Chart({ data, selectedStock }: ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#1e222d' },
        horzLines: { color: '#1e222d' },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#2a2e39',
      },
      rightPriceScale: {
        borderColor: '#2a2e39',
      },
      crosshair: {
        horzLine: {
          color: '#758696',
          labelBackgroundColor: '#4c525e',
        },
        vertLine: {
          color: '#758696',
          labelBackgroundColor: '#4c525e',
        },
      },
    })

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    // Add volume series
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

    // Handle resize
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

  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || data.length === 0) return

    // Convert data to chart format
    const candleData: CandlestickData[] = data.map((d) => ({
      time: d.time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }))

    const volumeData: HistogramData[] = data.map((d) => ({
      time: d.time,
      value: d.volume,
      color: d.close >= d.open ? '#26a69a80' : '#ef535080',
    }))

    candlestickSeriesRef.current.setData(candleData)
    volumeSeriesRef.current.setData(volumeData)

    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent()
    }
  }, [data])

  return (
    <div className="flex-1 flex flex-col bg-dark-card">
      {/* Chart header */}
      <div className="flex items-center gap-4 px-4 py-2 border-b border-dark-border">
        <div className="flex items-center gap-2">
          <span className="text-white font-semibold text-lg">
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

        <div className="flex items-center gap-2 ml-auto">
          <button className="px-3 py-1 text-sm text-dark-muted hover:text-white">1D</button>
          <button className="px-3 py-1 text-sm text-dark-muted hover:text-white">1W</button>
          <button className="px-3 py-1 text-sm text-white bg-dark-border rounded">1M</button>
          <button className="px-3 py-1 text-sm text-dark-muted hover:text-white">3M</button>
          <button className="px-3 py-1 text-sm text-dark-muted hover:text-white">1Y</button>
        </div>
      </div>

      {/* Chart container */}
      <div ref={chartContainerRef} className="flex-1" />
    </div>
  )
}
