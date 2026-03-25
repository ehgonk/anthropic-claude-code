"use client"

import dynamic from "next/dynamic"

const MapContainer = dynamic(() => import("@/components/map/MapContainer"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center bg-muted/20">
      <p className="text-sm text-muted-foreground">Carregando mapa...</p>
    </div>
  ),
})

interface MapLoaderProps {
  children?: React.ReactNode
}

export default function MapLoader({ children }: MapLoaderProps) {
  return <MapContainer>{children}</MapContainer>
}
