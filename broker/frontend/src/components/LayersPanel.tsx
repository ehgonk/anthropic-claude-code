import { Eye, EyeOff, Layers as LayersIcon, BarChart2, Activity } from 'lucide-react'

interface Layer {
  id: string
  label: string
  description: string
  icon: typeof BarChart2
}

interface LayersPanelProps {
  visibleLayers: string[]
  onToggleLayer: (layerId: string) => void
}

export default function LayersPanel({ visibleLayers, onToggleLayer }: LayersPanelProps) {
  const layers: Layer[] = [
    {
      id: 'volume',
      label: 'Volume',
      description: 'Mostrar barras de volume',
      icon: BarChart2,
    },
    {
      id: 'grid',
      label: 'Grid',
      description: 'Linhas de grade no gráfico',
      icon: LayersIcon,
    },
    {
      id: 'crosshair',
      label: 'Crosshair',
      description: 'Cursor de precisão',
      icon: Activity,
    },
    {
      id: 'price-labels',
      label: 'Rótulos de Preço',
      description: 'Mostrar valores no eixo Y',
      icon: BarChart2,
    },
    {
      id: 'time-labels',
      label: 'Rótulos de Tempo',
      description: 'Mostrar datas no eixo X',
      icon: BarChart2,
    },
    {
      id: 'last-price',
      label: 'Último Preço',
      description: 'Linha do preço atual',
      icon: Activity,
    },
  ]

  const overlays: Layer[] = [
    {
      id: 'ema-ribbon',
      label: 'EMA Ribbon',
      description: 'Faixa de médias exponenciais',
      icon: Activity,
    },
    {
      id: 'volume-profile',
      label: 'Volume Profile',
      description: 'Perfil de volume horizontal',
      icon: BarChart2,
    },
    {
      id: 'session-lines',
      label: 'Linhas de Sessão',
      description: 'Abertura/fechamento diário',
      icon: LayersIcon,
    },
  ]

  const renderLayerButton = (layer: Layer) => {
    const isVisible = visibleLayers.includes(layer.id)
    const Icon = layer.icon

    return (
      <button
        key={layer.id}
        onClick={() => onToggleLayer(layer.id)}
        className={`w-full text-left px-3 py-2 rounded transition-colors ${
          isVisible
            ? 'bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/50'
            : 'hover:bg-dark-border border border-transparent'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${
            isVisible
              ? 'bg-blue-600/30'
              : 'bg-dark-border'
          }`}>
            <Icon className={`w-4 h-4 ${
              isVisible ? 'text-blue-400' : 'text-dark-muted'
            }`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className={`text-sm font-medium ${
              isVisible ? 'text-dark-text' : 'text-dark-muted'
            }`}>
              {layer.label}
            </div>
            <div className="text-xs text-dark-muted mt-0.5">
              {layer.description}
            </div>
          </div>
          {isVisible ? (
            <Eye className="w-4 h-4 text-blue-400 flex-shrink-0" />
          ) : (
            <EyeOff className="w-4 h-4 text-dark-muted flex-shrink-0" />
          )}
        </div>
      </button>
    )
  }

  return (
    <div className="w-64 bg-dark-card border-r border-dark-border flex flex-col">
      <div className="px-4 py-3 border-b border-dark-border">
        <h3 className="text-sm font-semibold text-dark-text flex items-center gap-2">
          <LayersIcon className="w-4 h-4" />
          Camadas do Gráfico
        </h3>
        <p className="text-xs text-dark-muted mt-1">
          Gerenciar elementos visuais
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Basic Layers */}
        <div className="p-2">
          <h4 className="text-xs font-semibold text-dark-muted mb-2 uppercase px-2">Camadas Básicas</h4>
          <div className="space-y-1">
            {layers.map(renderLayerButton)}
          </div>
        </div>

        {/* Advanced Overlays */}
        <div className="p-2 border-t border-dark-border mt-2">
          <h4 className="text-xs font-semibold text-dark-muted mb-2 uppercase px-2">Overlays Avançados</h4>
          <div className="space-y-1">
            {overlays.map(renderLayerButton)}
          </div>
        </div>
      </div>

      <div className="px-4 py-3 border-t border-dark-border space-y-2">
        <div className="flex gap-2">
          <button
            onClick={() => {
              [...layers, ...overlays].forEach(layer => {
                if (!visibleLayers.includes(layer.id)) {
                  onToggleLayer(layer.id)
                }
              })
            }}
            className="flex-1 px-2 py-1.5 text-xs bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded transition-colors"
          >
            Mostrar Todas
          </button>
          <button
            onClick={() => {
              visibleLayers.forEach(layerId => onToggleLayer(layerId))
            }}
            className="flex-1 px-2 py-1.5 text-xs bg-dark-border hover:bg-dark-border/70 text-dark-muted rounded transition-colors"
          >
            Ocultar Todas
          </button>
        </div>
        <div className="text-xs text-dark-muted text-center">
          {visibleLayers.length} camada{visibleLayers.length !== 1 ? 's' : ''} visível{visibleLayers.length !== 1 ? 'eis' : ''}
        </div>
      </div>
    </div>
  )
}
