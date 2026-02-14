/**
 * Página Explorer — análise detalhada de um ativo específico.
 * Gráfico de preço + trades overlay + score gauge + breakdown.
 */

import { BarChart2, CandlestickChart, LineChart, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { InsiderTradeList } from "../components/InsiderTradeList";
import { PriceChart } from "../components/PriceChart";
import { ScoreBreakdown } from "../components/ScoreBreakdown";
import { ScoreGauge } from "../components/ScoreGauge";
import { SearchBar } from "../components/SearchBar";
import { useApi } from "../hooks/useApi";
import { api, type DashboardData, type StockPrice } from "../services/api";

type ChartType = "line" | "candlestick";
type Periodicity = "daily" | "weekly" | "monthly" | "yearly";

function aggregateByPeriod(prices: StockPrice[], period: Periodicity): StockPrice[] {
  if (period === "daily") return prices;

  const groups = new Map<string, StockPrice[]>();

  for (const p of prices) {
    const d = new Date(p.trade_date + "T12:00:00");
    let key: string;

    switch (period) {
      case "weekly": {
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1);
        const monday = new Date(d);
        monday.setDate(diff);
        key = monday.toISOString().slice(0, 10);
        break;
      }
      case "monthly":
        key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
        break;
      case "yearly":
        key = `${d.getFullYear()}`;
        break;
    }

    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(p);
  }

  return Array.from(groups.entries()).map(([, group]) => ({
    trade_date: group[group.length - 1].trade_date,
    open_price: group[0].open_price,
    high_price: Math.max(...group.map((g) => g.high_price)),
    low_price: Math.min(...group.map((g) => g.low_price)),
    close_price: group[group.length - 1].close_price,
    volume: group.reduce((sum, g) => sum + g.volume, 0),
    num_trades: group.reduce((sum, g) => sum + g.num_trades, 0),
  }));
}

export function ExplorerPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [ticker, setTicker] = useState(searchParams.get("ticker") || "");
  const [days, setDays] = useState(180);
  const [chartType, setChartType] = useState<ChartType>("line");
  const [periodicity, setPeriodicity] = useState<Periodicity>("daily");

  const { data, loading, error, refetch } = useApi(
    () => (ticker ? api.getDashboard(ticker, days) : Promise.resolve(null)),
    [ticker, days]
  );

  const handleSelect = (t: string) => {
    setTicker(t);
    setSearchParams({ ticker: t });
  };

  useEffect(() => {
    const t = searchParams.get("ticker");
    if (t && t !== ticker) setTicker(t);
  }, [searchParams]);

  const aggregatedPrices = data?.prices
    ? aggregateByPeriod(data.prices, periodicity)
    : [];

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
            Análise detalhada com overlay de trades
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
              <h2 className="card-title">Preço + Trades</h2>
              <div className="flex flex-wrap items-center gap-3">
                {/* Legenda */}
                <div className="flex gap-3 text-xs">
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" />
                    Compra
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
                    Venda
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2.5 w-6 rounded bg-blue-500/40" />
                    Vol. Mercado
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2.5 w-6 rounded bg-amber-500/60" />
                    Vol. Trade
                  </span>
                </div>

                {/* Tipo do gráfico */}
                <div className="flex rounded-lg border border-gray-700 overflow-hidden">
                  <button
                    onClick={() => setChartType("line")}
                    className={`flex items-center gap-1 px-2.5 py-1 text-xs transition-colors ${
                      chartType === "line"
                        ? "bg-brand-600/20 text-brand-400"
                        : "text-gray-500 hover:text-gray-300"
                    }`}
                  >
                    <LineChart className="h-3 w-3" />
                    Linha
                  </button>
                  <button
                    onClick={() => setChartType("candlestick")}
                    className={`flex items-center gap-1 px-2.5 py-1 text-xs border-l border-gray-700 transition-colors ${
                      chartType === "candlestick"
                        ? "bg-brand-600/20 text-brand-400"
                        : "text-gray-500 hover:text-gray-300"
                    }`}
                  >
                    <BarChart2 className="h-3 w-3" />
                    Candlestick
                  </button>
                </div>

                {/* Periodicidade */}
                <select
                  value={periodicity}
                  onChange={(e) => setPeriodicity(e.target.value as Periodicity)}
                  className="input text-xs !py-1"
                >
                  <option value="daily">Diário</option>
                  <option value="weekly">Semanal</option>
                  <option value="monthly">Mensal</option>
                  <option value="yearly">Anual</option>
                </select>
              </div>
            </div>
            <PriceChart
              prices={aggregatedPrices}
              insiderTrades={data.insider_trades}
              chartType={chartType}
              periodicity={periodicity}
            />
          </div>

          {/* Lista de trades */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                Negociações ({data.insider_trades.length})
              </h2>
            </div>
            <InsiderTradeList trades={data.insider_trades} />
          </div>
        </>
      )}
    </div>
  );
}
