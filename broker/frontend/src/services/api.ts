import axios from 'axios'
import type { Stock, CandleData } from '../App'

const API_URL = '/api'

// Configure axios to be more tolerant with Kaspersky interference
axios.defaults.validateStatus = (status) => {
  // Accept any status code that's not in the 4xx or 5xx range
  // This helps when antivirus software modifies responses
  return status >= 200 && status < 600
}

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
    try {
      const response = await axios.get(`${API_URL}/stocks`)
      console.log('✅ getStocks response:', response.status, response.data?.length)
      if (response.status === 200 && response.data) {
        return response.data
      }
      throw new Error(`Unexpected response: ${response.status}`)
    } catch (error) {
      console.warn('⚠️ axios failed, trying fetch...', error)
      // Fallback to fetch API (bypasses axios/Kaspersky issues)
      const response = await fetch(`${API_URL}/stocks`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return await response.json()
    }
  },

  async getCandleData(symbol: string): Promise<CandleData[]> {
    try {
      const response = await axios.get(`${API_URL}/stocks/${symbol}/candles`)
      if (response.status === 200 && response.data) {
        return response.data
      }
      throw new Error(`Unexpected response: ${response.status}`)
    } catch (error) {
      console.warn('⚠️ axios failed for candles, trying fetch...')
      const response = await fetch(`${API_URL}/stocks/${symbol}/candles`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return await response.json()
    }
  },

  async getLastUpdate(): Promise<LastUpdateInfo> {
    try {
      const response = await axios.get(`${API_URL}/last-update`)
      if (response.status === 200 && response.data) {
        return response.data
      }
      throw new Error(`Unexpected response: ${response.status}`)
    } catch (error) {
      console.warn('⚠️ axios failed for last-update, trying fetch...')
      const response = await fetch(`${API_URL}/last-update`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return await response.json()
    }
  },

  async ingestB3(year: number): Promise<IngestResult> {
    const response = await axios.post(`${API_URL}/ingest/b3/${year}`)
    return response.data
  },
}

export default api
