import { Check } from 'lucide-react'

interface IndicatorOption {
  id: string
  label: string
  description: string
}

interface IndicatorsPanelProps {
  activeIndicators: string[]
  onToggleIndicator: (indicatorId: string) => void
}

export default function IndicatorsPanel({ activeIndicators, onToggleIndicator }: IndicatorsPanelProps) {
  const indicators: IndicatorOption[] = [
    {
      id: 'sma20',
      label: 'SMA 20',
      description: 'Média Móvel Simples 20 períodos',
    },
    {
      id: 'sma50',
      label: 'SMA 50',
      description: 'Média Móvel Simples 50 períodos',
    },
    {
      id: 'sma200',
      label: 'SMA 200',
      description: 'Média Móvel Simples 200 períodos',
    },
    {
      id: 'ema9',
      label: 'EMA 9',
      description: 'Média Móvel Exponencial 9 períodos',
    },
    {
      id: 'ema21',
      label: 'EMA 21',
      description: 'Média Móvel Exponencial 21 períodos',
    },
    {
      id: 'rsi',
      label: 'RSI',
      description: 'Relative Strength Index (14 períodos)',
    },
    {
      id: 'macd',
      label: 'MACD',
      description: 'Moving Average Convergence Divergence',
    },
    {
      id: 'bollinger',
      label: 'Bollinger Bands',
      description: 'Bandas de Bollinger (20, 2)',
    },
  ]

  return (
    <div className="w-64 bg-dark-card border-r border-dark-border flex flex-col">
      <div className="px-4 py-3 border-b border-dark-border">
        <h3 className="text-sm font-semibold text-dark-text">Indicadores Técnicos</h3>
        <p className="text-xs text-dark-muted mt-1">
          Selecione os indicadores para o gráfico
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-2 space-y-1">
          {indicators.map((indicator) => {
            const isActive = activeIndicators.includes(indicator.id)

            return (
              <button
                key={indicator.id}
                onClick={() => onToggleIndicator(indicator.id)}
                className={`w-full text-left px-3 py-2 rounded transition-colors ${
                  isActive
                    ? 'bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/50'
                    : 'hover:bg-dark-border border border-transparent'
                }`}
              >
                <div className="flex items-start gap-2">
                  <div className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${
                    isActive
                      ? 'bg-blue-600 border-blue-600'
                      : 'border-dark-muted'
                  }`}>
                    {isActive && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium ${
                      isActive ? 'text-dark-text' : 'text-dark-muted'
                    }`}>
                      {indicator.label}
                    </div>
                    <div className="text-xs text-dark-muted mt-0.5">
                      {indicator.description}
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="px-4 py-3 border-t border-dark-border">
        <div className="text-xs text-dark-muted">
          {activeIndicators.length} indicador{activeIndicators.length !== 1 ? 'es' : ''} ativo{activeIndicators.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  )
}
