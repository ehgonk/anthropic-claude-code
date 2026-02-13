import axios from 'axios'
import type { Stock, CandleData } from '../App'

const API_URL = '/api'

const api = {
  async getStocks(): Promise<Stock[]> {
    const response = await axios.get(`${API_URL}/stocks`)
    return response.data
  },

  async getCandleData(symbol: string): Promise<CandleData[]> {
    const response = await axios.get(`${API_URL}/stocks/${symbol}/candles`)
    return response.data
  },
}

export default api
