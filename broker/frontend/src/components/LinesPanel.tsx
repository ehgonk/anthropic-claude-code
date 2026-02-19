import { Minus, TrendingUp, Circle, Square, Slash, Divide, Ruler } from 'lucide-react'

interface DrawingTool {
  id: string
  label: string
  description: string
  icon: typeof Minus
}

interface LinesPanelProps {
  activeTool: string | null
  onToolSelect: (toolId: string) => void
  onClearAll: () => void
}

export default function LinesPanel({ activeTool, onToolSelect, onClearAll }: LinesPanelProps) {
  const drawingTools: DrawingTool[] = [
    {
      id: 'trendline',
      label: 'Linha de Tendência',
      description: 'Desenhar linha de tendência',
      icon: TrendingUp,
    },
    {
      id: 'horizontal',
      label: 'Linha Horizontal',
      description: 'Linha de suporte/resistência',
      icon: Minus,
    },
    {
      id: 'vertical',
      label: 'Linha Vertical',
      description: 'Marcar eventos importantes',
      icon: Divide,
    },
    {
      id: 'ray',
      label: 'Raio',
      description: 'Linha infinita em uma direção',
      icon: Slash,
    },
    {
      id: 'fibonacci',
      label: 'Fibonacci',
      description: 'Retração de Fibonacci',
      icon: Ruler,
    },
    {
      id: 'circle',
      label: 'Círculo',
      description: 'Destacar áreas do gráfico',
      icon: Circle,
    },
    {
      id: 'rectangle',
      label: 'Retângulo',
      description: 'Marcar zonas de preço',
      icon: Square,
    },
  ]

  const colors = [
    { id: 'blue', label: 'Azul', value: '#3b82f6' },
    { id: 'green', label: 'Verde', value: '#10b981' },
    { id: 'red', label: 'Vermelho', value: '#ef4444' },
    { id: 'yellow', label: 'Amarelo', value: '#f59e0b' },
    { id: 'purple', label: 'Roxo', value: '#8b5cf6' },
    { id: 'white', label: 'Branco', value: '#ffffff' },
  ]

  return (
    <div className="w-64 bg-dark-card border-r border-dark-border flex flex-col">
      <div className="px-4 py-3 border-b border-dark-border">
        <h3 className="text-sm font-semibold text-dark-text">Ferramentas de Desenho</h3>
        <p className="text-xs text-dark-muted mt-1">
          Adicionar linhas e formas ao gráfico
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Drawing Tools */}
        <div className="p-2">
          <h4 className="text-xs font-semibold text-dark-muted mb-2 uppercase px-2">Ferramentas</h4>
          <div className="space-y-1">
            {drawingTools.map((tool) => {
              const isActive = activeTool === tool.id
              const Icon = tool.icon

              return (
                <button
                  key={tool.id}
                  onClick={() => onToolSelect(tool.id)}
                  className={`w-full text-left px-3 py-2 rounded transition-colors ${
                    isActive
                      ? 'bg-purple-600/20 hover:bg-purple-600/30 border border-purple-600/50'
                      : 'hover:bg-dark-border border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${
                      isActive
                        ? 'bg-purple-600/30'
                        : 'bg-dark-border'
                    }`}>
                      <Icon className={`w-4 h-4 ${
                        isActive ? 'text-purple-400' : 'text-dark-muted'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-medium ${
                        isActive ? 'text-dark-text' : 'text-dark-muted'
                      }`}>
                        {tool.label}
                      </div>
                      <div className="text-xs text-dark-muted mt-0.5">
                        {tool.description}
                      </div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Colors */}
        <div className="p-2 border-t border-dark-border mt-2">
          <h4 className="text-xs font-semibold text-dark-muted mb-2 uppercase px-2">Cores</h4>
          <div className="grid grid-cols-6 gap-2 px-2">
            {colors.map((color) => (
              <button
                key={color.id}
                className="w-8 h-8 rounded border-2 border-dark-border hover:border-dark-muted transition-colors"
                style={{ backgroundColor: color.value }}
                title={color.label}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="px-4 py-3 border-t border-dark-border space-y-2">
        <button
          onClick={onClearAll}
          className="w-full px-3 py-2 text-sm bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded transition-colors"
        >
          Limpar Todos os Desenhos
        </button>
        <div className="text-xs text-dark-muted text-center">
          {activeTool ? `${drawingTools.find(t => t.id === activeTool)?.label} selecionada` : 'Nenhuma ferramenta ativa'}
        </div>
      </div>
    </div>
  )
}
