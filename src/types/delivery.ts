export interface RawDeliveryRow {
  [key: string]: unknown
}

export interface GeocodedDelivery {
  address: string
  cep: string | null
  city: string | null
  state: string | null
  lat: number
  lng: number
  quantity: number
  period: string | null
}

export interface DeliveryAggregateData {
  h3Index: string
  resolution: number
  deliveryCount: number
  uniqueAddresses: number
  totalQuantity: number
  centerLat: number
  centerLng: number
  populationDensity: number | null
}

export interface ColumnMapping {
  address: string | null
  cep: string | null
  city: string | null
  state: string | null
  lat: string | null
  lng: string | null
  quantity: string | null
  period: string | null
}
