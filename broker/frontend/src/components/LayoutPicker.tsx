import { useState, useRef, useEffect } from 'react'
import { LayoutGrid } from 'lucide-react'

export interface PanelDef {
  colStart: number
  colEnd: number
  rowStart: number
  rowEnd: number
}

export interface GridLayout {
  id: string
  cols: number
  rows: number
  label: string
  panels?: PanelDef[]  // custom panel placement; if set, overrides simple grid
}

export const LAYOUTS: GridLayout[] = [
  // 1 panel
  { id: '1x1', cols: 1, rows: 1, label: '1' },
  // 2 panels
  { id: '2x1', cols: 2, rows: 1, label: '2' },
  { id: '1x2', cols: 1, rows: 2, label: '2' },
  // 3 panels
  { id: '3x1', cols: 3, rows: 1, label: '3' },
  { id: '1x3', cols: 1, rows: 3, label: '3' },
  // 3 panels: esquerda dividida (2x 1/4) + direita grande (1/2)
  {
    id: '3-left2-right1',
    cols: 2,
    rows: 2,
    label: '3',
    panels: [
      { colStart: 1, colEnd: 2, rowStart: 1, rowEnd: 2 }, // topo-esquerda (1/4)
      { colStart: 1, colEnd: 2, rowStart: 2, rowEnd: 3 }, // baixo-esquerda (1/4)
      { colStart: 2, colEnd: 3, rowStart: 1, rowEnd: 3 }, // direita (1/2)
    ],
  },
  // 4 panels
  { id: '2x2', cols: 2, rows: 2, label: '4' },
  { id: '4x1', cols: 4, rows: 1, label: '4' },
  { id: '1x4', cols: 1, rows: 4, label: '4' },
  // 6 panels
  { id: '3x2', cols: 3, rows: 2, label: '6' },
  { id: '2x3', cols: 2, rows: 3, label: '6' },
  // 8 panels
  { id: '4x2', cols: 4, rows: 2, label: '8' },
  { id: '2x4', cols: 2, rows: 4, label: '8' },
  // 9 panels
  { id: '3x3', cols: 3, rows: 3, label: '9' },
  // 12 panels
  { id: '4x3', cols: 4, rows: 3, label: '12' },
  { id: '3x4', cols: 3, rows: 4, label: '12' },
  // 16 panels
  { id: '4x4', cols: 4, rows: 4, label: '16' },
]

// Group layouts by total panel count
const GROUPS = [1, 2, 3, 4, 6, 8, 9, 12, 16]

function MiniGrid({ layout, active }: { layout: GridLayout; active: boolean }) {
  const { cols, rows, panels } = layout
  const color = active ? 'bg-blue-500/40' : 'bg-dark-border/60 hover:bg-dark-muted/40'

  if (panels) {
    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gridTemplateRows: `repeat(${rows}, 1fr)`,
          gap: '1px',
          width: 28,
          height: 20,
          flexShrink: 0,
        }}
        className={`rounded-sm overflow-hidden border ${active ? 'border-blue-500' : 'border-dark-border'}`}
      >
        {panels.map((p, i) => (
          <div
            key={i}
            style={{
              gridColumn: `${p.colStart} / ${p.colEnd}`,
              gridRow: `${p.rowStart} / ${p.rowEnd}`,
            }}
            className={color}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gridTemplateRows: `repeat(${rows}, 1fr)`,
        gap: '1px',
        width: 28,
        height: 20,
        flexShrink: 0,
      }}
      className={`rounded-sm overflow-hidden border ${active ? 'border-blue-500' : 'border-dark-border'}`}
    >
      {Array.from({ length: cols * rows }).map((_, i) => (
        <div key={i} className={color} />
      ))}
    </div>
  )
}

interface LayoutPickerProps {
  layout: GridLayout
  onSelect: (layout: GridLayout) => void
}

export default function LayoutPicker({ layout, onSelect }: LayoutPickerProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const totalPanels = layout.panels?.length ?? layout.cols * layout.rows

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        title={`Layout: ${layout.cols}×${layout.rows}`}
        className={`flex items-center gap-1.5 px-2 py-1 text-xs rounded transition-colors ${
          open
            ? 'text-dark-text bg-dark-border'
            : 'text-dark-muted hover:text-dark-text hover:bg-dark-border'
        }`}
      >
        <MiniGrid layout={layout} active={false} />
        <LayoutGrid className="w-3.5 h-3.5" />
        <span>{totalPanels} Tela{totalPanels > 1 ? 's' : ''}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 z-50 bg-dark-card border border-dark-border rounded-lg shadow-2xl p-3 min-w-[260px]">
          <div className="text-dark-muted text-xs mb-2 font-medium">Selecionar layout</div>
          <div className="space-y-1">
            {GROUPS.map(count => {
              const group = LAYOUTS.filter(l => (l.panels?.length ?? l.cols * l.rows) === count)
              if (group.length === 0) return null
              return (
                <div key={count} className="flex items-center gap-2">
                  <span className="text-dark-muted text-xs w-4 text-right flex-shrink-0">{count}</span>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {group.map(l => (
                      <button
                        key={l.id}
                        onClick={() => { onSelect(l); setOpen(false) }}
                        title={`${l.cols}×${l.rows}`}
                        className="hover:opacity-80 transition-opacity"
                      >
                        <MiniGrid layout={l} active={layout.id === l.id} />
                      </button>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
