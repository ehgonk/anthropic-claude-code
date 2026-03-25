export interface AnalysisResult {
  correlation: CorrelationData
  gaps: CoverageGap[]
  suggestions: PickupSuggestion[]
}

export interface CorrelationData {
  pearsonR: number
  dataPoints: Array<{
    h3Index: string
    population: number
    deliveries: number
    hasCoverage: boolean
  }>
}

export interface CoverageGap {
  h3Index: string
  deliveryCount: number
  population: number
  nearestPickupDistance: number // meters
  centerLat: number
  centerLng: number
}

export interface PickupSuggestion {
  lat: number
  lng: number
  score: number
  reasoning: string
  estimatedCoverage: number // number of deliveries within radius
  population: number
}
