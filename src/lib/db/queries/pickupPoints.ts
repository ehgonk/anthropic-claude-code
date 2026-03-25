import { prisma } from "@/lib/db/client"

export async function getPickupPoints(
  bbox?: { minLng: number; minLat: number; maxLng: number; maxLat: number },
  provider?: string
) {
  const where: Record<string, unknown> = { isActive: true }

  if (bbox) {
    where.lat = { gte: bbox.minLat, lte: bbox.maxLat }
    where.lng = { gte: bbox.minLng, lte: bbox.maxLng }
  }

  if (provider) {
    where.provider = provider
  }

  return prisma.pickupPoint.findMany({ where })
}
