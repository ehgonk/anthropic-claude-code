/**
 * Página Explorer — análise detalhada de um ativo específico.
 * Gráfico de preço + insiders overlay + score gauge + breakdown.
 */

import { LineChart, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { InsiderTradeList } from "../components/InsiderTradeList";
import { PriceChart } from "../components/PriceChart";
import { ScoreBreakdown } from "../components/ScoreBreakdown";
import { ScoreGauge } from "../components/ScoreGauge";
import { SearchBar } from "../components/SearchBar";
import { useApi } from "../hooks/useApi";
import { api, type DashboardData } from "../services/api";

export function ExplorerPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [ticker, setTicker] = useState(searchParams.get("ticker") || "");
  const [days, setDays] = useState(180);

  const { data, loading, error, refetch } = useApi(
    () => (ticker ? api.getDashboard(ticker, days) : Promise.resolve(null)),
    [ticker, days]
  );

  const handleSelect = (t: string) => {
    setTicker(t);
    setSearchParams({ ticker: t });
  };

  // Pega ticker da URL ao montar
  useEffect(() => {
    const t = searchParams.get("ticker");
    if (t && t !== ticker) setTicker(t);
  }, [searchParams]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            <LineChart className="mr-2 inline h-6 w-6" />
            Explorer
            {ticker && (
              <span className="ml-2 font-mono text-brand-400">{ticker}</span>
            )}
          </h1>
          <p className="text-sm text-gray-500">
            Análise detalhada com overlay de insiders
          </p>
        </div>

        <div className="flex items-center gap-3">
          <SearchBar onSelect={handleSelect} />
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="input"
          >
            <option value={30}>1 mês</option>
            <option value={90}>3 meses</option>
            <option value={180}>6 meses</option>
            <option value={365}>1 ano</option>
          </select>
        </div>
      </div>

      {/* Empty state */}
      {!ticker && (
        <div className="card flex h-64 flex-col items-center justify-center text-gray-500">
          <LineChart className="mb-3 h-12 w-12 opacity-30" />
          <p className="text-lg font-medium">Selecione um ativo</p>
          <p className="text-sm">Use a busca acima para começar a análise</p>
        </div>
      )}

      {/* Loading */}
      {ticker && loading && (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-brand-500" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card border-red-500/30 bg-red-500/5 text-center text-red-400">
          Erro ao carregar dados: {error}
        </div>
      )}

      {/* Content */}
      {ticker && data && !loading && (
        <>
          {/* Score + Gauge */}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="card flex flex-col items-center justify-center">
              {data.score ? (
                <ScoreGauge
                  score={data.score.total_score}
                  signal={data.score.signal}
                />
              ) : (
                <div className="py-8 text-center text-gray-500">
                  Score não calculado.
                  <br />
                  <span className="text-xs">Ingira dados e recalcule via Admin.</span>
                </div>
              )}
            </div>

            <div className="card lg:col-span-2">
              <div className="card-header">
                <h2 className="card-title">Composição do Score</h2>
              </div>
              {data.score ? (
                <ScoreBreakdown score={data.score} />
              ) : (
                <p className="text-sm text-gray-500">
                  Sem dados de score disponíveis
                </p>
              )}
            </div>
          </div>

          {/* Gráfico de preço */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                Preço + Trades de Insiders
              </h2>
              <div className="flex gap-3 text-xs">
                <span className="flex items-center gap-1">
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  Compra insider
                </span>
                <span className="flex items-center gap-1">
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
                  Venda insider
                </span>
              </div>
            </div>
            <PriceChart prices={data.prices} insiderTrades={data.insider_trades} />
          </div>

          {/* Lista de trades */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                Negociações de Insiders ({data.insider_trades.length})
              </h2>
            </div>
            <InsiderTradeList trades={data.insider_trades} />
          </div>
        </>
      )}
    </div>
  );
}
