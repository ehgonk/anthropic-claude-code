export interface ViewportState {
  longitude: number
  latitude: number
  zoom: number
}

export interface LayerVisibility {
  heatmap: boolean
  population: boolean
  pickupPoints: boolean
}

export type H3Resolution = 5 | 6 | 7
