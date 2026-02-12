/**
 * Gráfico de preço com marcadores de trades overlayed.
 * Suporta modo linha e candlestick, com volume em eixo secundário empilhado.
 * Usa Recharts (ComposedChart) para renderização.
 */

import { useMemo } from "react";
import {
  Area,
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { InsiderTrade, StockPrice } from "../services/api";

interface PriceChartProps {
  prices: StockPrice[];
  insiderTrades: InsiderTrade[];
  chartType?: "line" | "candlestick";
  periodicity?: "daily" | "weekly" | "monthly" | "yearly";
}

interface ChartDataPoint {
  date: string;
  label: string;
  price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  tradeVolume: number;
  candleBody: [number, number];
  candleWick: [number, number];
  bullish: boolean;
}

export function PriceChart({
  prices,
  insiderTrades,
  chartType = "line",
}: PriceChartProps) {
  if (prices.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-500">
        Sem dados de cotação disponíveis
      </div>
    );
  }

  const { insiderByDate, tradeVolumeByDate } = useMemo(() => {
    const byDate = new Map<string, InsiderTrade[]>();
    const volByDate = new Map<string, number>();

    for (const t of insiderTrades) {
      const existing = byDate.get(t.trade_date) || [];
      existing.push(t);
      byDate.set(t.trade_date, existing);
      volByDate.set(t.trade_date, (volByDate.get(t.trade_date) || 0) + t.volume);
    }

    return { insiderByDate: byDate, tradeVolumeByDate: volByDate };
  }, [insiderTrades]);

  const chartData: ChartDataPoint[] = useMemo(
    () =>
      prices.map((p) => {
        const bullish = p.close_price >= p.open_price;
        const tradeVol = tradeVolumeByDate.get(p.trade_date) || 0;

        return {
          date: p.trade_date,
          label: new Date(p.trade_date + "T12:00:00").toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "short",
          }),
          price: p.close_price,
          open: p.open_price,
          high: p.high_price,
          low: p.low_price,
          close: p.close_price,
          volume: p.volume,
          tradeVolume: tradeVol,
          candleBody: bullish
            ? [p.open_price, p.close_price]
            : [p.close_price, p.open_price],
          candleWick: [p.low_price, p.high_price],
          bullish,
        };
      }),
    [prices, tradeVolumeByDate]
  );

  const priceMap = useMemo(
    () => new Map(prices.map((p) => [p.trade_date, p.close_price])),
    [prices]
  );

  const { buyMarkers, sellMarkers } = useMemo(() => {
    const buys: { date: string; price: number; trades: InsiderTrade[] }[] = [];
    const sells: { date: string; price: number; trades: InsiderTrade[] }[] = [];

    for (const [dt, trades] of insiderByDate) {
      const price = priceMap.get(dt);
      if (!price) continue;
      const b = trades.filter((t) => t.trade_type === "Compra");
      const s = trades.filter((t) => t.trade_type === "Venda");
      if (b.length > 0) buys.push({ date: dt, price, trades: b });
      if (s.length > 0) sells.push({ date: dt, price, trades: s });
    }

    return { buyMarkers: buys, sellMarkers: sells };
  }, [insiderByDate, priceMap]);

  const formatCurrency = (val: number) =>
    `R$ ${val.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;

  const formatVolume = (val: number) => {
    if (val >= 1_000_000_000) return `R$${(val / 1_000_000_000).toFixed(1)}B`;
    if (val >= 1_000_000) return `R$${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `R$${(val / 1_000).toFixed(0)}K`;
    return `R$${val.toFixed(0)}`;
  };

  const maxVolume = Math.max(...chartData.map((d) => d.volume + d.tradeVolume), 1);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    const data = payload[0]?.payload as ChartDataPoint;
    if (!data) return null;

    const tradePercent =
      data.volume > 0 ? ((data.tradeVolume / data.volume) * 100).toFixed(2) : "0.00";

    return (
      <div className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-xs shadow-xl">
        <p className="mb-1.5 font-medium text-gray-300">Data: {label}</p>
        {chartType === "candlestick" ? (
          <>
            <p className="text-gray-400">
              Abertura: <span className="text-gray-200">{formatCurrency(data.open)}</span>
            </p>
            <p className="text-gray-400">
              Máxima: <span className="text-gray-200">{formatCurrency(data.high)}</span>
            </p>
            <p className="text-gray-400">
              Mínima: <span className="text-gray-200">{formatCurrency(data.low)}</span>
            </p>
            <p className="text-gray-400">
              Fechamento:{" "}
              <span className={data.bullish ? "text-emerald-400" : "text-red-400"}>
                {formatCurrency(data.close)}
              </span>
            </p>
          </>
        ) : (
          <p className="text-gray-400">
            Preço: <span className="text-blue-400">{formatCurrency(data.price)}</span>
          </p>
        )}
        <div className="mt-1.5 border-t border-gray-700 pt-1.5">
          <p className="text-gray-400">
            Vol. Negociado R$:{" "}
            <span className="text-blue-400">{formatVolume(data.volume)}</span>
          </p>
          {data.tradeVolume > 0 && (
            <>
              <p className="text-gray-400">
                Vol. Trade R$:{" "}
                <span className="text-amber-400">{formatVolume(data.tradeVolume)}</span>
              </p>
              <p className="text-gray-400">
                % Trade:{" "}
                <span className="text-amber-400">{tradePercent}%</span>
              </p>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#29a3ff" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#29a3ff" stopOpacity={0} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis
          dataKey="label"
          stroke="#6b7280"
          fontSize={11}
          tickLine={false}
          interval="preserveStartEnd"
        />
        {/* Eixo primário — preço */}
        <YAxis
          yAxisId="price"
          stroke="#6b7280"
          fontSize={11}
          tickLine={false}
          tickFormatter={(v) => `R$${v}`}
          domain={["auto", "auto"]}
        />
        {/* Eixo secundário — volume */}
        <YAxis
          yAxisId="volume"
          orientation="right"
          stroke="#4b5563"
          fontSize={10}
          tickLine={false}
          tickFormatter={formatVolume}
          domain={[0, maxVolume * 4]}
        />

        <Tooltip content={<CustomTooltip />} />

        {/* Volume empilhado — mercado + trade */}
        <Bar
          yAxisId="volume"
          dataKey="volume"
          stackId="vol"
          fill="#3b82f6"
          fillOpacity={0.25}
          isAnimationActive={false}
        />
        <Bar
          yAxisId="volume"
          dataKey="tradeVolume"
          stackId="vol"
          fill="#f59e0b"
          fillOpacity={0.5}
          isAnimationActive={false}
        />

        {/* Preço — modo Linha */}
        {chartType === "line" && (
          <Area
            yAxisId="price"
            type="monotone"
            dataKey="price"
            stroke="#29a3ff"
            strokeWidth={2}
            fill="url(#priceGradient)"
            dot={false}
            activeDot={{ r: 4, fill: "#29a3ff" }}
          />
        )}

        {/* Preço — modo Candlestick */}
        {chartType === "candlestick" && (
          <>
            <Bar
              yAxisId="price"
              dataKey="candleWick"
              barSize={2}
              isAnimationActive={false}
            >
              {chartData.map((entry, idx) => (
                <Cell
                  key={`wick-${idx}`}
                  fill={entry.bullish ? "#10b981" : "#ef4444"}
                />
              ))}
            </Bar>
            <Bar
              yAxisId="price"
              dataKey="candleBody"
              barSize={chartData.length > 60 ? 4 : chartData.length > 30 ? 6 : 10}
              isAnimationActive={false}
            >
              {chartData.map((entry, idx) => (
                <Cell
                  key={`body-${idx}`}
                  fill={entry.bullish ? "#10b981" : "#ef4444"}
                />
              ))}
            </Bar>
          </>
        )}

        {/* Marcadores de COMPRA (verde) */}
        {buyMarkers.map((m) => (
          <ReferenceDot
            key={`buy-${m.date}`}
            yAxisId="price"
            x={new Date(m.date + "T12:00:00").toLocaleDateString("pt-BR", {
              day: "2-digit",
              month: "short",
            })}
            y={m.price}
            r={5}
            fill="#10b981"
            stroke="#065f46"
            strokeWidth={2}
          />
        ))}

        {/* Marcadores de VENDA (vermelho) */}
        {sellMarkers.map((m) => (
          <ReferenceDot
            key={`sell-${m.date}`}
            yAxisId="price"
            x={new Date(m.date + "T12:00:00").toLocaleDateString("pt-BR", {
              day: "2-digit",
              month: "short",
            })}
            y={m.price}
            r={5}
            fill="#ef4444"
            stroke="#991b1b"
            strokeWidth={2}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
