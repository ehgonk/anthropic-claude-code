export type PickupProvider = "correios" | "clique_retire" | "manual"
export type PickupType = "agency" | "locker" | "partner"

export interface PickupPointData {
  id: string
  name: string
  provider: PickupProvider
  address: string | null
  city: string | null
  state: string | null
  lat: number
  lng: number
  type: PickupType
  isActive: boolean
}
