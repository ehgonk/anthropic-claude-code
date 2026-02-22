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

export interface DataStats {
  first_date: string | null
  last_date: string | null
  total_records: number
  total_stocks: number
  years: Array<{ year: number; count: number }>
  expected_start_year: number
  coverage_complete: boolean
}

export interface UpdateStatus {
  last_run: string | null
  last_success: string | null
  last_error: string | null
  is_running: boolean
  stats: any
}

export interface UpdateResult {
  status: string
  message: string
  total_years: number
  total_batches: number
  stocks: number
  prices: number
  batch_details: Array<{
    batch: number
    years: number[]
    stocks: number
    prices: number
  }>
  completed_at: string
}

const api = {
  async getStocks(): Promise<Stock[]> {
    console.log('📡 Fetching stocks...')
    const response = await fetch(`${API_URL}/stocks?page_size=100`, {
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
    // Backend returns { total, page, page_size, stocks: [...] }
    const stocks = data.stocks || data
    console.log('✅ getStocks success:', stocks.length, 'stocks')
    return stocks
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

  async getDataStats(): Promise<DataStats> {
    const response = await fetch(`${API_URL}/data/stats`, {
      headers: { 'Accept': 'application/json' },
      cache: 'no-cache'
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  },

  async getUpdateStatus(): Promise<UpdateStatus> {
    const response = await fetch(`${API_URL}/update/status`, {
      headers: { 'Accept': 'application/json' },
      cache: 'no-cache'
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  },

  async runUpdate(force: boolean = false, fullHistorical: boolean = false): Promise<UpdateResult> {
    const params = new URLSearchParams()
    if (force) params.append('force', 'true')
    if (fullHistorical) params.append('full_historical', 'true')

    const url = `${API_URL}/update/run${params.toString() ? '?' + params.toString() : ''}`

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Accept': 'application/json' },
      cache: 'no-cache'
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    return await response.json()
  },
}

export default api
