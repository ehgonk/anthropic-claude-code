import { prisma } from "@/lib/db/client"

export async function getPopulationCells(
  resolution: number,
  bbox?: { minLng: number; minLat: number; maxLng: number; maxLat: number }
) {
  const where: Record<string, unknown> = { resolution }

  if (bbox) {
    where.centerLat = { gte: bbox.minLat, lte: bbox.maxLat }
    where.centerLng = { gte: bbox.minLng, lte: bbox.maxLng }
  }

  return prisma.populationCell.findMany({ where })
}
