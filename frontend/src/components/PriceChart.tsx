/**
 * Gráfico de preço com marcadores de trades de insiders overlayed.
 * Usa Recharts para renderização.
 */

import {
  Area,
  AreaChart,
  CartesianGrid,
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
}

export function PriceChart({ prices, insiderTrades }: PriceChartProps) {
  if (prices.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-500">
        Sem dados de cotação disponíveis
      </div>
    );
  }

  // Mapeia insider trades por data para overlay
  const insiderByDate = new Map<string, InsiderTrade[]>();
  for (const t of insiderTrades) {
    const existing = insiderByDate.get(t.trade_date) || [];
    existing.push(t);
    insiderByDate.set(t.trade_date, existing);
  }

  // Dados do gráfico
  const chartData = prices.map((p) => ({
    date: p.trade_date,
    price: p.close_price,
    volume: p.volume,
    label: new Date(p.trade_date + "T12:00:00").toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
    }),
  }));

  // Encontra preço em uma data para posicionar marcadores
  const priceMap = new Map(prices.map((p) => [p.trade_date, p.close_price]));

  // Insider markers
  const buyMarkers: { date: string; price: number; trades: InsiderTrade[] }[] = [];
  const sellMarkers: { date: string; price: number; trades: InsiderTrade[] }[] = [];

  for (const [dt, trades] of insiderByDate) {
    const price = priceMap.get(dt);
    if (!price) continue;
    const buys = trades.filter((t) => t.trade_type === "Compra");
    const sells = trades.filter((t) => t.trade_type === "Venda");
    if (buys.length > 0) buyMarkers.push({ date: dt, price, trades: buys });
    if (sells.length > 0) sellMarkers.push({ date: dt, price, trades: sells });
  }

  const formatCurrency = (val: number) =>
    `R$ ${val.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
        <YAxis
          stroke="#6b7280"
          fontSize={11}
          tickLine={false}
          tickFormatter={(v) => `R$${v}`}
          domain={["auto", "auto"]}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f2937",
            border: "1px solid #374151",
            borderRadius: "8px",
            color: "#f3f4f6",
            fontSize: "12px",
          }}
          formatter={(value: number) => [formatCurrency(value), "Preço"]}
          labelFormatter={(label) => `Data: ${label}`}
        />

        <Area
          type="monotone"
          dataKey="price"
          stroke="#29a3ff"
          strokeWidth={2}
          fill="url(#priceGradient)"
          dot={false}
          activeDot={{ r: 4, fill: "#29a3ff" }}
        />

        {/* Marcadores de COMPRA de insiders (verde, acima) */}
        {buyMarkers.map((m) => (
          <ReferenceDot
            key={`buy-${m.date}`}
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

        {/* Marcadores de VENDA de insiders (vermelho, abaixo) */}
        {sellMarkers.map((m) => (
          <ReferenceDot
            key={`sell-${m.date}`}
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
      </AreaChart>
    </ResponsiveContainer>
  );
}
