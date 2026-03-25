import { create } from "zustand"
import type { ViewportState, LayerVisibility, H3Resolution } from "@/types/map"

interface MapState {
  viewport: ViewportState
  activeLayers: LayerVisibility
  pickupRadius: number // metros
  h3Resolution: H3Resolution
  setViewport: (v: Partial<ViewportState>) => void
  toggleLayer: (layer: keyof LayerVisibility) => void
  setPickupRadius: (r: number) => void
  setH3Resolution: (r: H3Resolution) => void
}

// Centro do Sudeste do Brasil (entre SP e RJ)
const DEFAULT_VIEWPORT: ViewportState = {
  longitude: -46.6333,
  latitude: -23.5505,
  zoom: 8,
}

export const useMapStore = create<MapState>((set) => ({
  viewport: DEFAULT_VIEWPORT,
  activeLayers: {
    heatmap: true,
    population: false,
    pickupPoints: true,
  },
  pickupRadius: 800, // 800m default (raio ótimo urbano)
  h3Resolution: 6,

  setViewport: (v) =>
    set((state) => ({ viewport: { ...state.viewport, ...v } })),

  toggleLayer: (layer) =>
    set((state) => ({
      activeLayers: {
        ...state.activeLayers,
        [layer]: !state.activeLayers[layer],
      },
    })),

  setPickupRadius: (r) => set({ pickupRadius: r }),
  setH3Resolution: (r) => set({ h3Resolution: r }),
}))
