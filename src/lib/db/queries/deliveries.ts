import { prisma } from "@/lib/db/client"

export async function getDeliveryAggregates(
  resolution: number,
  bbox?: { minLng: number; minLat: number; maxLng: number; maxLat: number }
) {
  const where: Record<string, unknown> = { resolution }

  if (bbox) {
    where.centerLat = { gte: bbox.minLat, lte: bbox.maxLat }
    where.centerLng = { gte: bbox.minLng, lte: bbox.maxLng }
  }

  return prisma.deliveryAggregate.findMany({ where })
}

export async function computeAggregates() {
  // Agrupa entregas por H3 res6 e insere/atualiza delivery_aggregates
  await prisma.$executeRaw`
    INSERT INTO delivery_aggregates
      ("h3Index", resolution, "deliveryCount", "uniqueAddresses", "totalQuantity", "centerLat", "centerLng", "updatedAt")
    SELECT
      "h3Res6"                AS "h3Index",
      6                       AS resolution,
      COUNT(*)                AS "deliveryCount",
      COUNT(DISTINCT address) AS "uniqueAddresses",
      SUM(quantity)           AS "totalQuantity",
      AVG(lat::float8)        AS "centerLat",
      AVG(lng::float8)        AS "centerLng",
      NOW()                   AS "updatedAt"
    FROM deliveries
    WHERE "h3Res6" IS NOT NULL AND lat IS NOT NULL
    GROUP BY "h3Res6"
    ON CONFLICT ("h3Index") DO UPDATE SET
      "deliveryCount"   = EXCLUDED."deliveryCount",
      "uniqueAddresses" = EXCLUDED."uniqueAddresses",
      "totalQuantity"   = EXCLUDED."totalQuantity",
      "centerLat"       = EXCLUDED."centerLat",
      "centerLng"       = EXCLUDED."centerLng",
      "updatedAt"       = EXCLUDED."updatedAt"
  `
}
