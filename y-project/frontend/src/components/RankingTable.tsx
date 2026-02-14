/**
 * Tabela de ranking — empresas ordenadas por atividade insider recente.
 */

import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { RankingItem } from "../services/api";

interface RankingTableProps {
  data: RankingItem[];
  onSelectTicker: (ticker: string) => void;
}

export function RankingTable({ data, onSelectTicker }: RankingTableProps) {
  const formatVolume = (val: number) => {
    const abs = Math.abs(val);
    if (abs >= 1_000_000) return `R$ ${(val / 1_000_000).toFixed(1)}M`;
    if (abs >= 1_000) return `R$ ${(val / 1_000).toFixed(0)}K`;
    return `R$ ${val.toFixed(0)}`;
  };

  const getSignalBadge = (signal: string) => {
    switch (signal) {
      case "COMPRA":
        return (
          <span className="badge badge-compra">
            <TrendingUp className="mr-1 h-3 w-3" /> COMPRA
          </span>
        );
      case "VENDA":
        return (
          <span className="badge badge-venda">
            <TrendingDown className="mr-1 h-3 w-3" /> VENDA
          </span>
        );
      default:
        return (
          <span className="badge badge-neutro">
            <Minus className="mr-1 h-3 w-3" /> NEUTRO
          </span>
        );
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 30) return "text-emerald-400";
    if (score <= -30) return "text-red-400";
    return "text-gray-400";
  };

  if (data.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500">
        Nenhum dado de ranking disponível. Ingira dados primeiro.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-xs uppercase tracking-wider text-gray-500">
            <th className="px-3 py-3">#</th>
            <th className="px-3 py-3">Ticker</th>
            <th className="px-3 py-3 hidden sm:table-cell">Empresa</th>
            <th className="px-3 py-3 text-center">Score</th>
            <th className="px-3 py-3 text-center">Sinal</th>
            <th className="px-3 py-3 text-center hidden md:table-cell">Compras 30d</th>
            <th className="px-3 py-3 text-center hidden md:table-cell">Vendas 30d</th>
            <th className="px-3 py-3 text-right hidden lg:table-cell">Volume Líq.</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <tr
              key={item.ticker}
              className="cursor-pointer border-b border-gray-800/50 transition-colors hover:bg-gray-800/50"
              onClick={() => onSelectTicker(item.ticker)}
            >
              <td className="px-3 py-3 text-gray-500">{idx + 1}</td>
              <td className="px-3 py-3 font-mono font-bold text-brand-400">
                {item.ticker}
              </td>
              <td className="px-3 py-3 hidden sm:table-cell max-w-[200px] truncate text-gray-300">
                {item.company_name}
              </td>
              <td className={`px-3 py-3 text-center font-bold ${getScoreColor(item.total_score)}`}>
                {item.total_score > 0 ? "+" : ""}
                {item.total_score.toFixed(0)}
              </td>
              <td className="px-3 py-3 text-center">{getSignalBadge(item.signal)}</td>
              <td className="px-3 py-3 text-center hidden md:table-cell text-emerald-400">
                {item.insider_buy_count_30d}
              </td>
              <td className="px-3 py-3 text-center hidden md:table-cell text-red-400">
                {item.insider_sell_count_30d}
              </td>
              <td
                className={`px-3 py-3 text-right hidden lg:table-cell font-mono ${
                  item.insider_net_volume_30d >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {formatVolume(item.insider_net_volume_30d)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
