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
    console.log('📡 Fetching stocks...')
    const response = await fetch(`${API_URL}/stocks`, {
      headers: { 'Accept': 'application/json' },
      cache: 'no-cache'
    })
    console.log('📡 getStocks status:', response.status)
    if (!response.ok) {
      const text = await response.text()
      console.error('❌ getStocks failed:', text)
      throw new Error(`HTTP ${response.status}: ${text}`)
    }
    const data = await response.json()
    console.log('✅ getStocks success:', data.length, 'stocks')
    return data
  },

  async getCandleData(symbol: string): Promise<CandleData[]> {
    const response = await fetch(`${API_URL}/stocks/${symbol}/candles`, {
      headers: { 'Accept': 'application/json' },
      cache: 'no-cache'
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  },

  async getLastUpdate(): Promise<LastUpdateInfo> {
    const response = await fetch(`${API_URL}/last-update`, {
      headers: { 'Accept': 'application/json' },
      cache: 'no-cache'
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  },

  async ingestB3(year: number): Promise<IngestResult> {
    const response = await fetch(`${API_URL}/ingest/b3/${year}`, {
      method: 'POST',
      headers: { 'Accept': 'application/json' },
      cache: 'no-cache'
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  },

  async getLastUpdateDate(): Promise<{ last_update: string; raw_date: string | null }> {
    const response = await fetch(`${API_URL}/update/last-update-date`, {
      headers: { 'Accept': 'application/json' },
      cache: 'no-cache'
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  },
}

export default api
