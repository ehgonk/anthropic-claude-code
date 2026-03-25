"use client"

import { useCallback, useRef } from "react"
import Map, { type MapRef } from "react-map-gl/maplibre"
import DeckGL from "@deck.gl/react"
import { useMapStore } from "@/stores/mapStore"
import { getResolutionForZoom } from "@/lib/geo/h3"
import { useDeliveryLayers } from "@/hooks/useDeliveryLayers"
import "maplibre-gl/dist/maplibre-gl.css"

const MAPTILER_KEY = process.env.NEXT_PUBLIC_MAPTILER_KEY

function getMapStyle() {
  if (MAPTILER_KEY) {
    return `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`
  }
  return "https://demotiles.maplibre.org/style.json"
}

interface MapContainerProps {
  children?: React.ReactNode
}

export default function MapContainer({ children }: MapContainerProps) {
  const mapRef = useRef<MapRef>(null)
  const { viewport, setViewport, setH3Resolution } = useMapStore()
  const deliveryLayers = useDeliveryLayers()

  const viewState = {
    longitude: viewport.longitude,
    latitude: viewport.latitude,
    zoom: viewport.zoom,
    pitch: 0,
    bearing: 0,
  }

  const handleViewStateChange = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ({ viewState: vs }: { viewState: any }) => {
      if (
        typeof vs.longitude === "number" &&
        typeof vs.latitude === "number" &&
        typeof vs.zoom === "number"
      ) {
        setViewport({ longitude: vs.longitude, latitude: vs.latitude, zoom: vs.zoom })
        setH3Resolution(getResolutionForZoom(vs.zoom))
      }
    },
    [setViewport, setH3Resolution]
  )

  return (
    <div className="relative w-full h-full">
      <DeckGL
        viewState={viewState}
        onViewStateChange={handleViewStateChange}
        controller
        layers={deliveryLayers}
        style={{ position: "absolute", top: "0", left: "0", right: "0", bottom: "0" }}
      >
        <Map
          ref={mapRef}
          mapStyle={getMapStyle()}
          reuseMaps
        />
      </DeckGL>

      {/* Controles sobrepostos */}
      {children}
    </div>
  )
}
