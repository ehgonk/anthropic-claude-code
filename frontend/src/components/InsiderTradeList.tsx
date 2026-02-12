/**
 * Lista de trades recentes de insiders com detalhes.
 */

import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { InsiderTrade } from "../services/api";

interface InsiderTradeListProps {
  trades: InsiderTrade[];
  showTicker?: boolean;
}

export function InsiderTradeList({ trades, showTicker = false }: InsiderTradeListProps) {
  const formatDate = (d: string) =>
    new Date(d + "T12:00:00").toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "2-digit",
    });

  const formatCurrency = (val: number) =>
    val.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

  const formatQty = (val: number) => {
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(0)}K`;
    return val.toFixed(0);
  };

  if (trades.length === 0) {
    return (
      <div className="py-6 text-center text-gray-500">
        Nenhuma negociação de insider encontrada
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
      {trades.map((t) => (
        <div
          key={t.id}
          className={`flex items-start gap-3 rounded-lg border p-3 transition-colors ${
            t.trade_type === "Compra"
              ? "border-emerald-500/20 bg-emerald-500/5"
              : "border-red-500/20 bg-red-500/5"
          }`}
        >
          {/* Ícone */}
          <div
            className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
              t.trade_type === "Compra" ? "bg-emerald-500/20" : "bg-red-500/20"
            }`}
          >
            {t.trade_type === "Compra" ? (
              <ArrowUpRight className="h-4 w-4 text-emerald-400" />
            ) : (
              <ArrowDownRight className="h-4 w-4 text-red-400" />
            )}
          </div>

          {/* Info */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              {showTicker && (
                <span className="font-mono text-xs font-bold text-brand-400">
                  {t.ticker}
                </span>
              )}
              <span className="truncate text-sm font-medium text-gray-200">
                {t.insider_name}
              </span>
            </div>
            <div className="mt-0.5 text-xs text-gray-500">
              {t.insider_role && <span>{t.insider_role} · </span>}
              {formatDate(t.trade_date)}
            </div>
          </div>

          {/* Valores */}
          <div className="shrink-0 text-right">
            <div
              className={`text-sm font-bold ${
                t.trade_type === "Compra" ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {formatCurrency(t.volume)}
            </div>
            <div className="text-xs text-gray-500">
              {formatQty(t.quantity)} @ {formatCurrency(t.price)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
