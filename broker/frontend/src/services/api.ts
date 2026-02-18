import axios from 'axios'
import type { Stock, CandleData } from '../App'

const API_URL = '/api'

export interface LastUpdateInfo {
  last_date: string | null
  first_date: string | null
  total_records: number
}

export interface IngestResult {
  status: string
  year: number
  stocks_processed: number
  price_records: number
  symbols: string[]
}

const api = {
  async getStocks(): Promise<Stock[]> {
    const response = await axios.get(`${API_URL}/stocks`)
    return response.data
  },

  async getCandleData(symbol: string): Promise<CandleData[]> {
    const response = await axios.get(`${API_URL}/stocks/${symbol}/candles`)
    return response.data
  },

  async getLastUpdate(): Promise<LastUpdateInfo> {
    const response = await axios.get(`${API_URL}/last-update`)
    return response.data
  },

  async ingestB3(year: number): Promise<IngestResult> {
    const response = await axios.post(`${API_URL}/ingest/b3/${year}`)
    return response.data
  },
}

export default api
