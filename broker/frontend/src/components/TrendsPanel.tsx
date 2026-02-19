import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface TrendOption {
  id: string
  label: string
  description: string
  icon: typeof TrendingUp
}

interface TrendsPanelProps {
  activeTrends: string[]
  onToggleTrend: (trendId: string) => void
}

export default function TrendsPanel({ activeTrends, onToggleTrend }: TrendsPanelProps) {
  const trends: TrendOption[] = [
    {
      id: 'uptrend',
      label: 'Tendência de Alta',
      description: 'Detectar tendências de alta no gráfico',
      icon: TrendingUp,
    },
    {
      id: 'downtrend',
      label: 'Tendência de Baixa',
      description: 'Detectar tendências de baixa no gráfico',
      icon: TrendingDown,
    },
    {
      id: 'sideways',
      label: 'Tendência Lateral',
      description: 'Identificar movimentos laterais',
      icon: Minus,
    },
    {
      id: 'support',
      label: 'Níveis de Suporte',
      description: 'Mostrar níveis de suporte automáticos',
      icon: TrendingUp,
    },
    {
      id: 'resistance',
      label: 'Níveis de Resistência',
      description: 'Mostrar níveis de resistência automáticos',
      icon: TrendingDown,
    },
  ]

  return (
    <div className="w-64 bg-dark-card border-r border-dark-border flex flex-col">
      <div className="px-4 py-3 border-b border-dark-border">
        <h3 className="text-sm font-semibold text-dark-text">Análise de Tendências</h3>
        <p className="text-xs text-dark-muted mt-1">
          Identificar padrões e tendências
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-2 space-y-1">
          {trends.map((trend) => {
            const isActive = activeTrends.includes(trend.id)
            const Icon = trend.icon

            return (
              <button
                key={trend.id}
                onClick={() => onToggleTrend(trend.id)}
                className={`w-full text-left px-3 py-2 rounded transition-colors ${
                  isActive
                    ? 'bg-green-600/20 hover:bg-green-600/30 border border-green-600/50'
                    : 'hover:bg-dark-border border border-transparent'
                }`}
              >
                <div className="flex items-start gap-2">
                  <div className={`mt-0.5 w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${
                    isActive
                      ? 'bg-green-600/30'
                      : 'bg-dark-border'
                  }`}>
                    <Icon className={`w-4 h-4 ${
                      isActive ? 'text-green-400' : 'text-dark-muted'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium ${
                      isActive ? 'text-dark-text' : 'text-dark-muted'
                    }`}>
                      {trend.label}
                    </div>
                    <div className="text-xs text-dark-muted mt-0.5">
                      {trend.description}
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
          {activeTrends.length} análise{activeTrends.length !== 1 ? 's' : ''} ativa{activeTrends.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  )
}
