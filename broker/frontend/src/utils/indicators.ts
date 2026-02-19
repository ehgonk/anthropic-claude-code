import { CandleData } from '../App'

export interface IndicatorData {
  time: string
  value: number
}

export interface BollingerBands {
  time: string
  upper: number
  middle: number
  lower: number
}

export interface MACDData {
  time: string
  macd: number
  signal: number
  histogram: number
}

/**
 * Calculate Simple Moving Average (SMA)
 */
export function calculateSMA(data: CandleData[], period: number): IndicatorData[] {
  const result: IndicatorData[] = []

  for (let i = period - 1; i < data.length; i++) {
    let sum = 0
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close
    }
    result.push({
      time: data[i].time,
      value: sum / period,
    })
  }

  return result
}

/**
 * Calculate Exponential Moving Average (EMA)
 */
export function calculateEMA(data: CandleData[], period: number): IndicatorData[] {
  const result: IndicatorData[] = []
  const multiplier = 2 / (period + 1)

  // First EMA is SMA
  let sum = 0
  for (let i = 0; i < period; i++) {
    sum += data[i].close
  }
  let ema = sum / period
  result.push({
    time: data[period - 1].time,
    value: ema,
  })

  // Calculate subsequent EMAs
  for (let i = period; i < data.length; i++) {
    ema = (data[i].close - ema) * multiplier + ema
    result.push({
      time: data[i].time,
      value: ema,
    })
  }

  return result
}

/**
 * Calculate Relative Strength Index (RSI)
 */
export function calculateRSI(data: CandleData[], period: number = 14): IndicatorData[] {
  const result: IndicatorData[] = []

  if (data.length < period + 1) return result

  // Calculate price changes
  const changes: number[] = []
  for (let i = 1; i < data.length; i++) {
    changes.push(data[i].close - data[i - 1].close)
  }

  // Calculate initial average gain and loss
  let avgGain = 0
  let avgLoss = 0
  for (let i = 0; i < period; i++) {
    if (changes[i] > 0) avgGain += changes[i]
    else avgLoss += Math.abs(changes[i])
  }
  avgGain /= period
  avgLoss /= period

  // Calculate RSI
  for (let i = period; i < changes.length; i++) {
    const currentGain = changes[i] > 0 ? changes[i] : 0
    const currentLoss = changes[i] < 0 ? Math.abs(changes[i]) : 0

    avgGain = (avgGain * (period - 1) + currentGain) / period
    avgLoss = (avgLoss * (period - 1) + currentLoss) / period

    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
    const rsi = 100 - (100 / (1 + rs))

    result.push({
      time: data[i + 1].time,
      value: rsi,
    })
  }

  return result
}

/**
 * Calculate MACD (Moving Average Convergence Divergence)
 */
export function calculateMACD(
  data: CandleData[],
  fastPeriod: number = 12,
  slowPeriod: number = 26,
  signalPeriod: number = 9
): MACDData[] {
  const result: MACDData[] = []

  // Calculate EMAs
  const fastEMA = calculateEMA(data, fastPeriod)
  const slowEMA = calculateEMA(data, slowPeriod)

  // Calculate MACD line
  const macdLine: IndicatorData[] = []
  for (let i = 0; i < slowEMA.length; i++) {
    const fastIndex = fastEMA.findIndex(f => f.time === slowEMA[i].time)
    if (fastIndex !== -1) {
      macdLine.push({
        time: slowEMA[i].time,
        value: fastEMA[fastIndex].value - slowEMA[i].value,
      })
    }
  }

  // Calculate signal line (EMA of MACD)
  const multiplier = 2 / (signalPeriod + 1)
  if (macdLine.length < signalPeriod) return result

  let signalEMA = 0
  for (let i = 0; i < signalPeriod; i++) {
    signalEMA += macdLine[i].value
  }
  signalEMA /= signalPeriod

  result.push({
    time: macdLine[signalPeriod - 1].time,
    macd: macdLine[signalPeriod - 1].value,
    signal: signalEMA,
    histogram: macdLine[signalPeriod - 1].value - signalEMA,
  })

  for (let i = signalPeriod; i < macdLine.length; i++) {
    signalEMA = (macdLine[i].value - signalEMA) * multiplier + signalEMA
    result.push({
      time: macdLine[i].time,
      macd: macdLine[i].value,
      signal: signalEMA,
      histogram: macdLine[i].value - signalEMA,
    })
  }

  return result
}

/**
 * Calculate Bollinger Bands
 */
export function calculateBollingerBands(
  data: CandleData[],
  period: number = 20,
  stdDev: number = 2
): BollingerBands[] {
  const result: BollingerBands[] = []
  const sma = calculateSMA(data, period)

  for (let i = 0; i < sma.length; i++) {
    const dataIndex = i + period - 1

    // Calculate standard deviation
    let sumSquaredDiff = 0
    for (let j = 0; j < period; j++) {
      const diff = data[dataIndex - j].close - sma[i].value
      sumSquaredDiff += diff * diff
    }
    const stdDevValue = Math.sqrt(sumSquaredDiff / period)

    result.push({
      time: sma[i].time,
      upper: sma[i].value + (stdDev * stdDevValue),
      middle: sma[i].value,
      lower: sma[i].value - (stdDev * stdDevValue),
    })
  }

  return result
}
