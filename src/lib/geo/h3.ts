import { latLngToCell, cellToLatLng } from "h3-js"
import type { H3Resolution } from "@/types/map"

export function assignH3Indices(lat: number, lng: number) {
  return {
    h3Res5: latLngToCell(lat, lng, 5),
    h3Res6: latLngToCell(lat, lng, 6),
    h3Res7: latLngToCell(lat, lng, 7),
  }
}

export function getH3Center(h3Index: string): [number, number] {
  const [lat, lng] = cellToLatLng(h3Index)
  return [lat, lng]
}

export function getResolutionForZoom(zoom: number): H3Resolution {
  if (zoom >= 11) return 7
  if (zoom >= 8) return 6
  return 5
}
