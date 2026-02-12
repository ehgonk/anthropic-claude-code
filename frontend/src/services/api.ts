/**
 * Cliente HTTP para a API do Radar Insider.
 * Todas as chamadas passam pelo proxy do Vite em dev → /api/*
 */

const BASE = "/api";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// === Types ===

export interface Company {
  id: number;
  ticker: string;
  name: string;
  cnpj?: string;
  sector?: string;
}

export interface StockPrice {
  trade_date: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  num_trades: number;
}

export interface InsiderTrade {
  id: number;
  ticker: string;
  company_name: string;
  insider_name: string;
  insider_role?: string;
  trade_type: "Compra" | "Venda";
  quantity: number;
  price: number;
  volume: number;
  trade_date: string;
  report_date?: string;
}

export interface Score {
  ticker: string;
  calc_date: string;
  insider_score: number;
  short_score: number;
  flow_score: number;
  momentum_score: number;
  total_score: number;
  signal: "COMPRA" | "NEUTRO" | "VENDA";
  insider_buy_count_30d: number;
  insider_sell_count_30d: number;
  insider_net_volume_30d: number;
}

export interface RankingItem {
  ticker: string;
  company_name: string;
  total_score: number;
  signal: string;
  insider_buy_count_30d: number;
  insider_sell_count_30d: number;
  insider_net_volume_30d: number;
}

export interface DashboardData {
  prices: StockPrice[];
  insider_trades: InsiderTrade[];
  score: Score | null;
}

export interface Summary {
  total_companies: number;
  total_insider_trades: number;
  recent_buys_30d: number;
  recent_sells_30d: number;
  top_signal: string;
  last_update: string | null;
}

// === API Calls ===

export const api = {
  getCompanies: (search?: string) =>
    fetchJSON<Company[]>(`/companies${search ? `?search=${encodeURIComponent(search)}` : ""}`),

  getPrices: (ticker: string, days = 365) =>
    fetchJSON<StockPrice[]>(`/prices/${ticker}?days=${days}`),

  getInsiderTrades: (ticker?: string, days = 90) =>
    fetchJSON<InsiderTrade[]>(
      `/insider-trades?days=${days}${ticker ? `&ticker=${ticker}` : ""}`
    ),

  getRanking: (limit = 20, order: "asc" | "desc" = "desc") =>
    fetchJSON<RankingItem[]>(`/scores/ranking?limit=${limit}&order=${order}`),

  getScore: (ticker: string) => fetchJSON<Score>(`/scores/${ticker}`),

  getScoreHistory: (ticker: string, days = 90) =>
    fetchJSON<Score[]>(`/scores/${ticker}/history?days=${days}`),

  getDashboard: (ticker: string, days = 180) =>
    fetchJSON<DashboardData>(`/dashboard/${ticker}?days=${days}`),

  getSummary: () => fetchJSON<Summary>("/summary"),

  triggerIngest: (source: "cvm" | "b3", year: number) =>
    fetchJSON<{ status: string; records_inserted: number }>(
      `/ingest/${source}/${year}`
    ),

  recalculateScores: () =>
    fetchJSON<{ status: string; scores_calculated: number }>("/scores/recalculate"),
};
