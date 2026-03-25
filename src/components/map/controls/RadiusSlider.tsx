"use client"

import { Slider } from "@/components/ui/slider"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useMapStore } from "@/stores/mapStore"

const MIN = 300
const MAX = 5000
const STEP = 100

function formatRadius(meters: number): string {
  return meters >= 1000
    ? `${(meters / 1000).toFixed(1)} km`
    : `${meters} m`
}

export default function RadiusSlider() {
  const { pickupRadius, setPickupRadius } = useMapStore()

  return (
    <Card className="w-56 shadow-md">
      <CardHeader className="py-3 px-4">
        <CardTitle className="text-sm flex items-center justify-between">
          <span>Raio de Cobertura</span>
          <span className="font-mono text-primary">{formatRadius(pickupRadius)}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="py-2 px-4">
        <Slider
          min={MIN}
          max={MAX}
          step={STEP}
          value={[pickupRadius]}
          onValueChange={(value) => {
            const v = Array.isArray(value) ? value[0] : value
            if (v !== undefined) setPickupRadius(v as number)
          }}
          aria-label="Raio de cobertura dos pontos de retirada"
        />
        <div className="flex justify-between mt-1">
          <span className="text-[10px] text-muted-foreground">{formatRadius(MIN)}</span>
          <span className="text-[10px] text-muted-foreground">{formatRadius(MAX)}</span>
        </div>
      </CardContent>
    </Card>
  )
}
