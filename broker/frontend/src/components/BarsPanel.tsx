import { BarChart3, Activity } from 'lucide-react'

interface TimeframeOption {
  id: string
  label: string
  value: string
}

interface CandleTypeOption {
  id: string
  label: string
  description: string
  icon: typeof BarChart3
}

interface BarsPanelProps {
  selectedTimeframe: string
  selectedCandleType: string
  onTimeframeChange: (timeframe: string) => void
  onCandleTypeChange: (type: string) => void
}

export default function BarsPanel({
  selectedTimeframe,
  selectedCandleType,
  onTimeframeChange,
  onCandleTypeChange
}: BarsPanelProps) {
  const timeframes: TimeframeOption[] = [
    { id: '1m', label: '1 Min', value: '1m' },
    { id: '5m', label: '5 Min', value: '5m' },
    { id: '15m', label: '15 Min', value: '15m' },
    { id: '30m', label: '30 Min', value: '30m' },
    { id: '1h', label: '1 Hora', value: '1h' },
    { id: '4h', label: '4 Horas', value: '4h' },
    { id: '1d', label: '1 Dia', value: '1d' },
    { id: '1w', label: '1 Semana', value: '1w' },
    { id: '1M', label: '1 Mês', value: '1M' },
  ]

  const candleTypes: CandleTypeOption[] = [
    {
      id: 'candlestick',
      label: 'Candlestick',
      description: 'Gráfico de velas tradicional',
      icon: BarChart3,
    },
    {
      id: 'bars',
      label: 'Barras',
      description: 'Gráfico de barras OHLC',
      icon: BarChart3,
    },
    {
      id: 'line',
      label: 'Linha',
      description: 'Gráfico de linha simples',
      icon: Activity,
    },
  ]

  return (
    <div className="w-64 bg-dark-card border-r border-dark-border flex flex-col">
      <div className="px-4 py-3 border-b border-dark-border">
        <h3 className="text-sm font-semibold text-dark-text">Configuração de Barras</h3>
        <p className="text-xs text-dark-muted mt-1">
          Timeframe e tipo de gráfico
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Timeframes Section */}
        <div className="p-4 border-b border-dark-border">
          <h4 className="text-xs font-semibold text-dark-muted mb-2 uppercase">Timeframe</h4>
          <div className="grid grid-cols-3 gap-1">
            {timeframes.map((timeframe) => (
              <button
                key={timeframe.id}
                onClick={() => onTimeframeChange(timeframe.value)}
                className={`px-2 py-1.5 text-xs rounded transition-colors ${
                  selectedTimeframe === timeframe.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-dark-border text-dark-muted hover:bg-dark-border/70 hover:text-dark-text'
                }`}
              >
                {timeframe.label}
              </button>
            ))}
          </div>
        </div>

        {/* Candle Types Section */}
        <div className="p-2">
          <h4 className="text-xs font-semibold text-dark-muted mb-2 uppercase px-2">Tipo de Gráfico</h4>
          <div className="space-y-1">
            {candleTypes.map((type) => {
              const isActive = selectedCandleType === type.id
              const Icon = type.icon

              return (
                <button
                  key={type.id}
                  onClick={() => onCandleTypeChange(type.id)}
                  className={`w-full text-left px-3 py-2 rounded transition-colors ${
                    isActive
                      ? 'bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/50'
                      : 'hover:bg-dark-border border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${
                      isActive
                        ? 'bg-blue-600/30'
                        : 'bg-dark-border'
                    }`}>
                      <Icon className={`w-4 h-4 ${
                        isActive ? 'text-blue-400' : 'text-dark-muted'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-medium ${
                        isActive ? 'text-dark-text' : 'text-dark-muted'
                      }`}>
                        {type.label}
                      </div>
                      <div className="text-xs text-dark-muted mt-0.5">
                        {type.description}
                      </div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      <div className="px-4 py-3 border-t border-dark-border">
        <div className="text-xs text-dark-muted">
          {selectedTimeframe} • {candleTypes.find(t => t.id === selectedCandleType)?.label}
        </div>
      </div>
    </div>
  )
}
