"use client"

import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useMapStore } from "@/stores/mapStore"
import type { LayerVisibility } from "@/types/map"

const LAYER_LABELS: Record<keyof LayerVisibility, string> = {
  heatmap: "Heatmap de Entregas",
  population: "Densidade Populacional",
  pickupPoints: "Pontos de Retirada",
}

export default function LayerControl() {
  const { activeLayers, toggleLayer } = useMapStore()

  return (
    <Card className="w-56 shadow-md">
      <CardHeader className="py-3 px-4">
        <CardTitle className="text-sm">Camadas</CardTitle>
      </CardHeader>
      <CardContent className="py-2 px-4 space-y-3">
        {(Object.keys(activeLayers) as (keyof LayerVisibility)[]).map((layer) => (
          <div key={layer} className="flex items-center justify-between gap-2">
            <span className="text-xs text-muted-foreground">
              {LAYER_LABELS[layer]}
            </span>
            <Switch
              checked={activeLayers[layer]}
              onCheckedChange={() => toggleLayer(layer)}
              aria-label={`Toggle ${LAYER_LABELS[layer]}`}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
