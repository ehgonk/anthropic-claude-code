-- CreateTable
CREATE TABLE "deliveries" (
    "id" TEXT NOT NULL,
    "address" TEXT NOT NULL,
    "cep" VARCHAR(8),
    "city" VARCHAR(100),
    "state" VARCHAR(2),
    "lat" DECIMAL(10,8),
    "lng" DECIMAL(11,8),
    "h3Res5" VARCHAR(15),
    "h3Res6" VARCHAR(15),
    "h3Res7" VARCHAR(15),
    "quantity" INTEGER NOT NULL DEFAULT 1,
    "period" TEXT,
    "rawData" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "deliveries_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "delivery_aggregates" (
    "h3Index" VARCHAR(15) NOT NULL,
    "resolution" INTEGER NOT NULL,
    "deliveryCount" INTEGER NOT NULL DEFAULT 0,
    "uniqueAddresses" INTEGER NOT NULL DEFAULT 0,
    "totalQuantity" INTEGER NOT NULL DEFAULT 0,
    "centerLat" DECIMAL(10,8) NOT NULL,
    "centerLng" DECIMAL(11,8) NOT NULL,
    "populationDensity" DECIMAL(65,30),
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "delivery_aggregates_pkey" PRIMARY KEY ("h3Index")
);

-- CreateTable
CREATE TABLE "pickup_points" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "externalId" TEXT,
    "address" TEXT,
    "city" TEXT,
    "state" VARCHAR(2),
    "lat" DECIMAL(10,8) NOT NULL,
    "lng" DECIMAL(11,8) NOT NULL,
    "h3Res7" VARCHAR(15),
    "type" TEXT NOT NULL,
    "metadata" JSONB,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "pickup_points_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "population_cells" (
    "h3Index" VARCHAR(15) NOT NULL,
    "resolution" INTEGER NOT NULL,
    "population" INTEGER NOT NULL,
    "year" INTEGER NOT NULL,
    "centerLat" DECIMAL(10,8) NOT NULL,
    "centerLng" DECIMAL(11,8) NOT NULL,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "population_cells_pkey" PRIMARY KEY ("h3Index")
);

-- CreateIndex
CREATE INDEX "deliveries_h3Res6_idx" ON "deliveries"("h3Res6");

-- CreateIndex
CREATE INDEX "deliveries_cep_idx" ON "deliveries"("cep");

-- CreateIndex
CREATE INDEX "delivery_aggregates_resolution_idx" ON "delivery_aggregates"("resolution");

-- CreateIndex
CREATE INDEX "pickup_points_provider_idx" ON "pickup_points"("provider");

-- CreateIndex
CREATE INDEX "pickup_points_state_idx" ON "pickup_points"("state");

-- CreateIndex
CREATE INDEX "population_cells_resolution_idx" ON "population_cells"("resolution");
