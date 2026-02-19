import {
  TrendingUp,
  BarChart3,
  LineChart,
  Activity,
  List,
  Layers
} from 'lucide-react'

interface LeftBarProps {
  activeTool: string | null
  onToolSelect: (tool: string) => void
}

export default function LeftBar({ activeTool, onToolSelect }: LeftBarProps) {
  const tools = [
    { id: 'trends', icon: TrendingUp, label: 'Trends' },
    { id: 'bars', icon: BarChart3, label: 'Bars' },
    { id: 'lines', icon: LineChart, label: 'Lines' },
    { id: 'indicators', icon: Activity, label: 'Indicators' },
    { id: 'watchlist', icon: List, label: 'Watchlist' },
    { id: 'layers', icon: Layers, label: 'Layers' },
  ]

  return (
    <div className="w-14 bg-dark-card border-r border-dark-border flex flex-col items-center py-3 gap-2">
      {tools.map((tool) => (
        <button
          key={tool.id}
          onClick={() => {
            console.log('🔧 Tool clicked:', tool.id)
            console.log('🔧 Current activeTool:', activeTool)
            onToolSelect(tool.id)
          }}
          className={`p-2 rounded transition-colors group relative ${
            activeTool === tool.id
              ? 'bg-blue-600 hover:bg-blue-700'
              : 'hover:bg-dark-border'
          }`}
          title={tool.label}
        >
          <tool.icon className={`w-5 h-5 ${
            activeTool === tool.id
              ? 'text-white'
              : 'text-dark-muted group-hover:text-dark-text'
          }`} />
        </button>
      ))}
    </div>
  )
}
