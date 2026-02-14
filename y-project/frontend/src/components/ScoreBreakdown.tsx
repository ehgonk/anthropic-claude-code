/**
 * Breakdown visual dos 4 componentes do score.
 */

import type { Score } from "../services/api";

interface ScoreBreakdownProps {
  score: Score;
}

interface BarProps {
  label: string;
  value: number;
  weight: string;
  color: string;
}

function ScoreBar({ label, value, weight, color }: BarProps) {
  const width = Math.abs(value) / 2; // 0-100 → 0-50% width
  const isPositive = value >= 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-400">
          {label} <span className="text-gray-600">({weight})</span>
        </span>
        <span className={value >= 0 ? "text-emerald-400" : "text-red-400"}>
          {value > 0 ? "+" : ""}
          {value.toFixed(1)}
        </span>
      </div>
      <div className="flex h-2 items-center">
        {/* Lado esquerdo (negativo) */}
        <div className="flex h-full w-1/2 justify-end">
          {!isPositive && (
            <div
              className="h-full rounded-l-full"
              style={{
                width: `${width}%`,
                backgroundColor: color,
                opacity: 0.7,
              }}
            />
          )}
        </div>
        {/* Divisor central */}
        <div className="h-3 w-px bg-gray-600" />
        {/* Lado direito (positivo) */}
        <div className="flex h-full w-1/2">
          {isPositive && (
            <div
              className="h-full rounded-r-full"
              style={{
                width: `${width}%`,
                backgroundColor: color,
                opacity: 0.7,
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  return (
    <div className="space-y-4">
      <ScoreBar
        label="Trades Administradores"
        value={score.insider_score}
        weight="40%"
        color="#8b5cf6"
      />
      <ScoreBar
        label="Short Interest"
        value={score.short_score}
        weight="20%"
        color="#f59e0b"
      />
      <ScoreBar
        label="Fluxo Estrangeiro"
        value={score.flow_score}
        weight="20%"
        color="#06b6d4"
      />
      <ScoreBar
        label="Momentum Técnico"
        value={score.momentum_score}
        weight="20%"
        color="#ec4899"
      />

      {/* Resumo numérico */}
      <div className="mt-4 flex justify-between border-t border-gray-800 pt-3 text-xs text-gray-500">
        <span>Compras 30d: <strong className="text-emerald-400">{score.insider_buy_count_30d}</strong></span>
        <span>Vendas 30d: <strong className="text-red-400">{score.insider_sell_count_30d}</strong></span>
      </div>
    </div>
  );
}
