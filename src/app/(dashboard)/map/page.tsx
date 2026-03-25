import MapLoader from "@/components/map/MapLoader"
import LayerControl from "@/components/map/controls/LayerControl"
import RadiusSlider from "@/components/map/controls/RadiusSlider"

export default function MapPage() {
  return (
    <div className="relative h-full w-full">
      <MapLoader>
        {/* Painel de controles — canto superior direito */}
        <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
          <LayerControl />
          <RadiusSlider />
        </div>
      </MapLoader>
    </div>
  )
}
