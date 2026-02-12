/**
 * Página de ranking completo com filtros.
 */

import { ArrowDownAZ, ArrowUpAZ, ListOrdered } from "lucide-react";
import { useState } from "react";
import { RankingTable } from "../components/RankingTable";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

export function RankingPage() {
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [limit, setLimit] = useState(50);

  const { data, loading, refetch } = useApi(
    () => api.getRanking(limit, order),
    [limit, order]
  );

  const handleTickerSelect = (ticker: string) => {
    window.location.href = `/explorer?ticker=${ticker}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            <ListOrdered className="mr-2 inline h-6 w-6" />
            Ranking Insider
          </h1>
          <p className="text-sm text-gray-500">
            Empresas ordenadas por score de atividade insider
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setOrder(order === "desc" ? "asc" : "desc")}
            className="btn-primary flex items-center gap-2"
          >
            {order === "desc" ? (
              <>
                <ArrowDownAZ className="h-4 w-4" /> Maiores primeiro
              </>
            ) : (
              <>
                <ArrowUpAZ className="h-4 w-4" /> Menores primeiro
              </>
            )}
          </button>

          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="input"
          >
            <option value={20}>Top 20</option>
            <option value={50}>Top 50</option>
            <option value={100}>Top 100</option>
          </select>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-gray-800" />
            ))}
          </div>
        ) : (
          <RankingTable data={data ?? []} onSelectTicker={handleTickerSelect} />
        )}
      </div>
    </div>
  );
}
