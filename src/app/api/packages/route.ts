import { NextRequest, NextResponse } from "next/server"
import { getDeliveryAggregates } from "@/lib/db/queries/deliveries"

export const runtime = "nodejs"

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl

  const resolution = parseInt(searchParams.get("resolution") ?? "6", 10)

  const minLat = searchParams.get("minLat")
  const maxLat = searchParams.get("maxLat")
  const minLng = searchParams.get("minLng")
  const maxLng = searchParams.get("maxLng")

  const bbox =
    minLat && maxLat && minLng && maxLng
      ? {
          minLat: parseFloat(minLat),
          maxLat: parseFloat(maxLat),
          minLng: parseFloat(minLng),
          maxLng: parseFloat(maxLng),
        }
      : undefined

  try {
    const aggregates = await getDeliveryAggregates(resolution, bbox)

    return NextResponse.json(
      {
        aggregates: aggregates.map((a) => ({
          h3Index: a.h3Index,
          resolution: a.resolution,
          deliveryCount: a.deliveryCount,
          uniqueAddresses: a.uniqueAddresses,
          totalQuantity: a.totalQuantity,
          centerLat: Number(a.centerLat),
          centerLng: Number(a.centerLng),
          populationDensity: a.populationDensity !== null ? Number(a.populationDensity) : null,
        })),
      },
      {
        headers: {
          // Cache de 5 minutos no navegador, revalidação em background
          "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
        },
      }
    )
  } catch (error) {
    console.error("[/api/packages]", error)
    return NextResponse.json({ error: "Erro ao buscar dados de entregas" }, { status: 500 })
  }
}
