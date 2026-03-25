/**
 * scripts/import-olist.ts
 *
 * Importa o dataset Olist Brazilian E-Commerce (Kaggle) para o banco Neon.
 * Coloque os CSVs em data/olist/ antes de executar.
 *
 * Uso: npx tsx scripts/import-olist.ts
 *
 * Arquivos necessários em data/olist/:
 *   olist_customers_dataset.csv
 *   olist_geolocation_dataset.csv
 *   olist_order_items_dataset.csv
 *   olist_orders_dataset.csv
 */

import dotenv from "dotenv"
dotenv.config({ path: ".env.local" })

import * as fs from "fs"
import * as readline from "readline"
import * as path from "path"
import { latLngToCell } from "h3-js"
import { neon } from "@neondatabase/serverless"

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const DATA_DIR = path.join(process.cwd(), "data", "olist")
const BATCH_SIZE = 500

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface GeoAccumulator {
  sumLat: number
  sumLng: number
  count: number
  city: string
  state: string
}

interface GeoEntry {
  lat: number
  lng: number
  city: string
  state: string
}

interface CustomerEntry {
  zip: string
  city: string
  state: string
}

interface DeliveryInsert {
  address: string
  cep: string | null
  city: string | null
  state: string | null
  lat: number
  lng: number
  h3Res5: string
  h3Res6: string
  h3Res7: string
  quantity: number
  period: string | null
}

// ---------------------------------------------------------------------------
// CSV helpers
// ---------------------------------------------------------------------------

/** Parseia uma linha CSV respeitando campos entre aspas. */
function parseLine(line: string): string[] {
  const result: string[] = []
  let current = ""
  let inQuotes = false

  for (const char of line) {
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === "," && !inQuotes) {
      result.push(current.trim())
      current = ""
    } else {
      current += char
    }
  }
  result.push(current.trim())
  return result
}

/** Itera sobre cada linha do CSV chamando onRow (sem coletar em memória). */
async function streamCSV(
  filename: string,
  onRow: (row: Record<string, string>, lineNum: number) => void
): Promise<number> {
  const filePath = path.join(DATA_DIR, filename)

  if (!fs.existsSync(filePath)) {
    throw new Error(`Arquivo não encontrado: ${filePath}\nColoque os CSVs em data/olist/`)
  }

  const rl = readline.createInterface({
    input: fs.createReadStream(filePath, { encoding: "utf8" }),
    crlfDelay: Infinity,
  })

  let headers: string[] = []
  let lineNum = 0

  for await (const line of rl) {
    if (!line.trim()) continue

    if (lineNum === 0) {
      headers = parseLine(line)
      lineNum++
      continue
    }

    const values = parseLine(line)
    const row: Record<string, string> = {}
    headers.forEach((h, i) => {
      row[h] = values[i] ?? ""
    })

    onRow(row, lineNum)
    lineNum++
  }

  return lineNum - 1 // total de linhas de dados
}

// ---------------------------------------------------------------------------
// Step 1 — Geolocalização: zip prefix → lat/lng médio
// ---------------------------------------------------------------------------

async function buildGeoMap(): Promise<Map<string, GeoEntry>> {
  console.log("📍 [1/4] Lendo olist_geolocation_dataset.csv...")

  const accum = new Map<string, GeoAccumulator>()

  const total = await streamCSV("olist_geolocation_dataset.csv", (row) => {
    const zip = row["geolocation_zip_code_prefix"]?.padStart(5, "0") ?? ""
    const lat = parseFloat(row["geolocation_lat"] ?? "")
    const lng = parseFloat(row["geolocation_lng"] ?? "")
    const state = (row["geolocation_state"] ?? "").toUpperCase()

    if (!zip || isNaN(lat) || isNaN(lng)) return

    // Filtra coordenadas claramente fora do Brasil
    if (lat < -33.8 || lat > 5.3 || lng < -73.9 || lng > -34.8) return

    const existing = accum.get(zip)
    if (existing) {
      existing.sumLat += lat
      existing.sumLng += lng
      existing.count++
    } else {
      accum.set(zip, {
        sumLat: lat,
        sumLng: lng,
        count: 1,
        city: row["geolocation_city"] ?? "",
        state,
      })
    }
  })

  const geoMap = new Map<string, GeoEntry>()
  for (const [zip, acc] of accum) {
    geoMap.set(zip, {
      lat: acc.sumLat / acc.count,
      lng: acc.sumLng / acc.count,
      city: acc.city,
      state: acc.state,
    })
  }

  console.log(`   ✅ ${geoMap.size} prefixos únicos de CEP (de ${total.toLocaleString()} linhas)`)
  return geoMap
}

// ---------------------------------------------------------------------------
// Step 2 — Clientes: customer_id → {zip, city, state}
// ---------------------------------------------------------------------------

async function buildCustomerMap(): Promise<Map<string, CustomerEntry>> {
  console.log("👤 [2/4] Lendo olist_customers_dataset.csv...")

  const customerMap = new Map<string, CustomerEntry>()

  const total = await streamCSV("olist_customers_dataset.csv", (row) => {
    const id = row["customer_id"] ?? ""
    const zip = row["customer_zip_code_prefix"]?.padStart(5, "0") ?? ""
    if (!id || !zip) return

    customerMap.set(id, {
      zip,
      city: row["customer_city"] ?? "",
      state: (row["customer_state"] ?? "").toUpperCase(),
    })
  })

  console.log(`   ✅ ${customerMap.size.toLocaleString()} clientes (de ${total.toLocaleString()} linhas)`)
  return customerMap
}

// ---------------------------------------------------------------------------
// Step 3 — Itens: order_id → contagem de itens
// ---------------------------------------------------------------------------

async function buildItemCountMap(): Promise<Map<string, number>> {
  console.log("📦 [3/4] Lendo olist_order_items_dataset.csv...")

  const itemMap = new Map<string, number>()

  const total = await streamCSV("olist_order_items_dataset.csv", (row) => {
    const orderId = row["order_id"] ?? ""
    if (!orderId) return
    itemMap.set(orderId, (itemMap.get(orderId) ?? 0) + 1)
  })

  console.log(`   ✅ ${itemMap.size.toLocaleString()} pedidos com itens (de ${total.toLocaleString()} linhas)`)
  return itemMap
}

// ---------------------------------------------------------------------------
// Step 4 — Pedidos: join + H3 + insert em lotes (versão async com flush)
// ---------------------------------------------------------------------------

/**
 * streamCSVAsync suporta await no callback (serializado linha a linha),
 * necessário para fazer flush do lote de inserts durante a leitura.
 */
async function streamCSVAsync(
  filename: string,
  onRow: (row: Record<string, string>) => Promise<void>
): Promise<number> {
  const filePath = path.join(DATA_DIR, filename)

  if (!fs.existsSync(filePath)) {
    throw new Error(`Arquivo não encontrado: ${filePath}`)
  }

  const rl = readline.createInterface({
    input: fs.createReadStream(filePath, { encoding: "utf8" }),
    crlfDelay: Infinity,
  })

  let headers: string[] = []
  let lineNum = 0

  for await (const line of rl) {
    if (!line.trim()) continue

    if (lineNum === 0) {
      headers = parseLine(line)
      lineNum++
      continue
    }

    const values = parseLine(line)
    const row: Record<string, string> = {}
    headers.forEach((h, i) => {
      row[h] = values[i] ?? ""
    })

    await onRow(row)
    lineNum++
  }

  return lineNum - 1
}

async function importOrdersAsync(
  sql: ReturnType<typeof neon>,
  geoMap: Map<string, GeoEntry>,
  customerMap: Map<string, CustomerEntry>,
  itemMap: Map<string, number>
): Promise<void> {
  console.log("🚚 [4/4] Processando olist_orders_dataset.csv...")

  let batch: DeliveryInsert[] = []
  let inserted = 0
  let skipped = 0
  let batchCount = 0

  const flushBatch = async () => {
    if (batch.length === 0) return
    batchCount++

    // Bulk insert via unnest — sem transação, compatível com HTTP mode
    const addresses  = batch.map((d) => d.address)
    const ceps       = batch.map((d) => d.cep)
    const cities     = batch.map((d) => d.city)
    const states     = batch.map((d) => d.state)
    const lats       = batch.map((d) => d.lat)
    const lngs       = batch.map((d) => d.lng)
    const h3Res5s    = batch.map((d) => d.h3Res5)
    const h3Res6s    = batch.map((d) => d.h3Res6)
    const h3Res7s    = batch.map((d) => d.h3Res7)
    const quantities = batch.map((d) => d.quantity)
    const periods    = batch.map((d) => d.period)

    await sql`
      INSERT INTO deliveries
        (id, address, cep, city, state, lat, lng, "h3Res5", "h3Res6", "h3Res7", quantity, period, "createdAt")
      SELECT
        gen_random_uuid()::text,
        unnest(${addresses}::text[]),
        unnest(${ceps}::text[]),
        unnest(${cities}::text[]),
        unnest(${states}::text[]),
        unnest(${lats}::float8[]),
        unnest(${lngs}::float8[]),
        unnest(${h3Res5s}::text[]),
        unnest(${h3Res6s}::text[]),
        unnest(${h3Res7s}::text[]),
        unnest(${quantities}::int[]),
        unnest(${periods}::text[]),
        now()
    `

    inserted += batch.length
    batch = []
    console.log(`   Lote ${batchCount}: ${inserted.toLocaleString()} inseridos | ${skipped.toLocaleString()} ignorados`)
  }

  await streamCSVAsync("olist_orders_dataset.csv", async (row) => {
    if (row["order_status"] !== "delivered") {
      skipped++
      return
    }

    const orderId = row["order_id"] ?? ""
    const customerId = row["customer_id"] ?? ""
    const purchaseDate = row["order_purchase_timestamp"] ?? ""

    const customer = customerMap.get(customerId)
    if (!customer) {
      skipped++
      return
    }

    const geo = geoMap.get(customer.zip)
    if (!geo) {
      skipped++
      return
    }

    const period = purchaseDate.length >= 7 ? purchaseDate.substring(0, 7) : null
    const quantity = itemMap.get(orderId) ?? 1

    const h3Res5 = latLngToCell(geo.lat, geo.lng, 5)
    const h3Res6 = latLngToCell(geo.lat, geo.lng, 6)
    const h3Res7 = latLngToCell(geo.lat, geo.lng, 7)

    const address = [customer.city, customer.state].filter(Boolean).join(", ") || customer.zip

    batch.push({
      address,
      cep: customer.zip,
      city: customer.city || geo.city,
      state: customer.state || geo.state,
      lat: geo.lat,
      lng: geo.lng,
      h3Res5,
      h3Res6,
      h3Res7,
      quantity,
      period,
    })

    if (batch.length >= BATCH_SIZE) {
      await flushBatch()
    }
  })

  // Flush do lote restante
  await flushBatch()

  console.log(
    `\n   ✅ Total inserido: ${inserted.toLocaleString()} | Ignorados (não-delivered/sem geo): ${skipped.toLocaleString()}`
  )
}

// ---------------------------------------------------------------------------
// Step 5 — Recalcular agregados H3
// ---------------------------------------------------------------------------

async function recomputeAggregates(sql: ReturnType<typeof neon>): Promise<void> {
  console.log("🔢 [5/5] Recalculando delivery_aggregates (H3 res6)...")

  await sql`
    INSERT INTO delivery_aggregates
      ("h3Index", resolution, "deliveryCount", "uniqueAddresses", "totalQuantity", "centerLat", "centerLng", "updatedAt")
    SELECT
      "h3Res6"               AS "h3Index",
      6                      AS resolution,
      COUNT(*)               AS "deliveryCount",
      COUNT(DISTINCT address) AS "uniqueAddresses",
      SUM(quantity)          AS "totalQuantity",
      AVG(lat::float8)       AS "centerLat",
      AVG(lng::float8)       AS "centerLng",
      NOW()                  AS "updatedAt"
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

  const result = await sql`SELECT COUNT(*) AS count FROM delivery_aggregates`
  const row = result[0] as { count: string }
  console.log(`   ✅ ${parseInt(row.count).toLocaleString()} células H3 agregadas`)
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const connectionString = process.env["DATABASE_URL"]

  if (!connectionString || connectionString.includes("xxxx")) {
    throw new Error(
      "❌ DATABASE_URL não configurada.\nEdite .env.local com a connection string do Neon."
    )
  }

  if (!fs.existsSync(DATA_DIR)) {
    throw new Error(
      `❌ Diretório não encontrado: ${DATA_DIR}\nCrie a pasta e coloque os CSVs do Olist lá.`
    )
  }

  console.log("🗺️  MVP Maps — Importador Olist")
  console.log(`📂 Diretório: ${DATA_DIR}\n`)

  const sql = neon(connectionString)

  const geoMap = await buildGeoMap()
  const customerMap = await buildCustomerMap()
  const itemMap = await buildItemCountMap()
  await importOrdersAsync(sql, geoMap, customerMap, itemMap)
  await recomputeAggregates(sql)

  console.log("\n🎉 Importação concluída com sucesso!")
  console.log("   Acesse o mapa para visualizar o heatmap de entregas.")
}

main().catch((err) => {
  console.error("\n❌ Erro durante a importação:", err)
  process.exit(1)
})
