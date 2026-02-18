import {
  TrendingUp,
  BarChart3,
  LineChart,
  Activity,
  List,
  Layers
} from 'lucide-react'

export default function LeftBar() {
  const tools = [
    { icon: TrendingUp, label: 'Trends' },
    { icon: BarChart3, label: 'Bars' },
    { icon: LineChart, label: 'Lines' },
    { icon: Activity, label: 'Indicators' },
    { icon: List, label: 'Watchlist' },
    { icon: Layers, label: 'Layers' },
  ]

  return (
    <div className="w-14 bg-dark-card border-r border-dark-border flex flex-col items-center py-3 gap-2">
      {tools.map((tool, index) => (
        <button
          key={index}
          className="p-2 hover:bg-dark-border rounded transition-colors group relative"
          title={tool.label}
        >
          <tool.icon className="w-5 h-5 text-dark-muted group-hover:text-dark-text" />
        </button>
      ))}
    </div>
  )
}
