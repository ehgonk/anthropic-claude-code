"use client"

import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { H3HexagonLayer } from "@deck.gl/geo-layers"
import { useMapStore } from "@/stores/mapStore"
import type { DeliveryAggregateData } from "@/types/delivery"

interface PackagesResponse {
  aggregates: DeliveryAggregateData[]
}

async function fetchPackages(resolution: number): Promise<PackagesResponse> {
  const res = await fetch(`/api/packages?resolution=${resolution}`)
  if (!res.ok) throw new Error("Falha ao buscar dados de entregas")
  return res.json() as Promise<PackagesResponse>
}

/** Interpola cor YlOrRd (amarelo → laranja → vermelho) normalizada por t ∈ [0, 1]. */
function heatColor(t: number): [number, number, number, number] {
  // 3 paradas: amarelo claro → laranja → vermelho escuro
  if (t < 0.5) {
    const s = t * 2
    return [
      Math.round(255),
      Math.round(255 - s * (255 - 141)),
      Math.round(178 - s * 178),
      Math.round(120 + s * 60),
    ]
  } else {
    const s = (t - 0.5) * 2
    return [
      Math.round(255 - s * (255 - 189)),
      Math.round(141 - s * 141),
      Math.round(0),
      Math.round(180 + s * 40),
    ]
  }
}

export function useDeliveryLayers() {
  const { activeLayers, h3Resolution } = useMapStore()

  const { data } = useQuery({
    queryKey: ["packages", h3Resolution],
    queryFn: () => fetchPackages(h3Resolution),
    staleTime: 5 * 60 * 1000, // 5 minutos
    enabled: activeLayers.heatmap,
  })

  const layers = useMemo(() => {
    if (!activeLayers.heatmap || !data?.aggregates.length) return []

    const aggregates = data.aggregates
    const maxQuantity = Math.max(...aggregates.map((a) => a.totalQuantity))

    const layer = new H3HexagonLayer<DeliveryAggregateData>({
      id: "delivery-heatmap",
      data: aggregates,
      getHexagon: (d) => d.h3Index,
      getFillColor: (d) => heatColor(Math.sqrt(d.totalQuantity / maxQuantity)),
      getElevation: 0,
      extruded: false,
      filled: true,
      stroked: false,
      pickable: true,
      updateTriggers: {
        getFillColor: [maxQuantity],
      },
    })

    return [layer]
  }, [activeLayers.heatmap, data, h3Resolution])

  return layers
}
