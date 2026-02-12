/**
 * Página principal — visão geral do mercado + atividade insider recente.
 */

import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Building2,
  TrendingUp,
  Users,
} from "lucide-react";
import { useState } from "react";
import { InsiderTradeList } from "../components/InsiderTradeList";
import { RankingTable } from "../components/RankingTable";
import { SearchBar } from "../components/SearchBar";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

function StatCard({ label, value, icon, color, subtitle }: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
          {icon}
        </div>
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-xl font-bold">{value}</p>
          {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}

export function HomePage() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  const { data: summary, loading: summaryLoading } = useApi(
    () => api.getSummary(),
    []
  );

  const { data: ranking, loading: rankingLoading } = useApi(
    () => api.getRanking(10),
    []
  );

  const { data: recentTrades, loading: tradesLoading } = useApi(
    () => api.getInsiderTrades(undefined, 30),
    []
  );

  const handleTickerSelect = (ticker: string) => {
    setSelectedTicker(ticker);
    window.location.href = `/explorer?ticker=${ticker}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Visão Geral</h1>
          <p className="text-sm text-gray-500">
            Monitoramento de trades de administradores — B3/CVM
          </p>
        </div>
        <SearchBar onSelect={handleTickerSelect} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Empresas"
          value={summary?.total_companies ?? "—"}
          icon={<Building2 className="h-5 w-5 text-brand-400" />}
          color="bg-brand-500/15"
        />
        <StatCard
          label="Total de Trades"
          value={summary?.total_insider_trades?.toLocaleString("pt-BR") ?? "—"}
          icon={<BarChart3 className="h-5 w-5 text-purple-400" />}
          color="bg-purple-500/15"
        />
        <StatCard
          label="Compras 30d"
          value={summary?.recent_buys_30d ?? "—"}
          icon={<ArrowUpRight className="h-5 w-5 text-emerald-400" />}
          color="bg-emerald-500/15"
        />
        <StatCard
          label="Vendas 30d"
          value={summary?.recent_sells_30d ?? "—"}
          icon={<ArrowDownRight className="h-5 w-5 text-red-400" />}
          color="bg-red-500/15"
        />
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Ranking */}
        <div className="card lg:col-span-2">
          <div className="card-header">
            <h2 className="card-title">
              <TrendingUp className="mr-2 inline h-4 w-4" />
              Top Scores — Trade Activity
            </h2>
          </div>
          {rankingLoading ? (
            <LoadingPulse />
          ) : (
            <RankingTable data={ranking ?? []} onSelectTicker={handleTickerSelect} />
          )}
        </div>

        {/* Recent trades */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <Users className="mr-2 inline h-4 w-4" />
              Trades Recentes
            </h2>
          </div>
          {tradesLoading ? (
            <LoadingPulse />
          ) : (
            <InsiderTradeList trades={recentTrades ?? []} showTicker />
          )}
        </div>
      </div>
    </div>
  );
}

function LoadingPulse() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="h-10 animate-pulse rounded-lg bg-gray-800" />
      ))}
    </div>
  );
}
