export interface PopulationCellData {
  h3Index: string
  resolution: number
  population: number
  year: number
  centerLat: number
  centerLng: number
}

export interface WorldPopResponse {
  status: string
  data: WorldPopCell[]
}

export interface WorldPopCell {
  lat: number
  lng: number
  population: number
}
