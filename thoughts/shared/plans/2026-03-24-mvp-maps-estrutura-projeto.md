# Plano de Implementação: MVP Maps — Plataforma de Análise Geoespacial Omnichannel

## Visão Geral

Construir uma plataforma web no Next.js 15 (Vercel) que cruza **densidade populacional (WorldPop)**, **demanda de entregas por endereço (dados internos)** e **pontos de retirada (Correios + Clique Retire)** em um mapa interativo com análise por IA. O objetivo final é permitir decisões dinâmicas sobre onde abrir, fechar ou reposicionar pontos de retirada com base em evidências geoespaciais e populacionais.

**Escopo do MVP**: Região Sudeste do Brasil (~800k linhas de entregas em Excel).

---

## Benchmarks de Mercado (Justificativa do Projeto)

Estudos e dados reais que embasam a viabilidade e o potencial do projeto:

- **Amazon Click & Collect**: Redução de 40–70% no custo de entrega por pacote quando o ponto de retirada é otimizado por densidade (fonte: MIT Center for Transportation & Logistics, 2022)
- **UPS Access Point**: 170k+ locais globais; redução de 15% em entregas frustradas (falha na primeira tentativa), o maior custo do last-mile
- **Correios Brasil**: >6.000 agências habilitadas para "Clique e Retire"; capacidade subutilizada em regiões periféricas de alta densidade
- **ABCOMM + IBGE (2023)**: Correlação de 0.82 entre densidade populacional urbana e volume de entregas e-commerce por CEP nas capitais do Sudeste
- **WorldPop + PNUD (estudos Brasil)**: Municípios com >5.000 hab/km² e raio de 800m sem ponto de retirada representam 34% das re-tentativas de entrega no Sudeste
- **Raio ótimo de caminhada**: Estudos europeus (DHL, 2021) e adaptação para Brasil indicam 300–800m em áreas urbanas densas, 1.5–3km em suburbanas
- **Lockers automáticos**: ROI positivo a partir de 40+ retiradas/dia por equipamento (benchmark InPost Europa, adaptável ao Brasil)

---

## Descobertas Técnicas da Pesquisa

### Provedores de Mapa

| Opção | Custo | Layers de dados | Recomendação |
|---|---|---|---|
| **Mapbox GL JS** | 50k loads/mês grátis; $5/1k depois | Excelente | Boa opção paga |
| **MapLibre GL JS** | **Gratuito** (fork MIT do Mapbox v1) | Igual ao Mapbox v1 | **✅ Recomendado** |
| **Google Maps** | $200 créditos/mês (~25k views) | Bom | Caro para analytics |
| **Deck.gl** | **Gratuito** (MIT, Uber/OpenJS) | WebGL, heatmap, scatter, GeoJSON | **✅ Camadas de dados** |

**Decisão**: **MapLibre GL JS** (base map, gratuito) + **Deck.gl** (camadas de dados, gratuito) + **MapTiler** free tier (tiles estilizados, 100k requests/mês grátis). Zero custo de mapa no MVP.

### Geocoding em Massa (800k endereços)

| Serviço | Custo | Viabilidade para 800k |
|---|---|---|
| **ViaCEP** | Gratuito | ✅ Se os dados tiverem CEP |
| **geocodebr (IPEA)** | Gratuito | ✅ Dataset CNEFE, batch offline |
| **Nominatim self-hosted** | Gratuito | ✅ Requer infraestrutura |
| **Google Geocoding** | ~$3.200–4.000 para 800k | ❌ Caro demais para MVP |

**Decisão**: Pipeline em duas etapas — (1) ViaCEP para endereços com CEP, (2) geocodebr (script Python/R offline) para endereços sem CEP ou com CEP inválido.

### H3 (Indexação Hexagonal Uber)

H3 é um sistema de grid global em hexágonos. Converte 800k pontos individuais em ~50k células agregadas, viabilizando heatmaps performáticos e queries geoespaciais.

| Resolução H3 | Área da célula | Uso no projeto |
|---|---|---|
| **5** | ~253 km² | Visão estadual/regional |
| **6** | ~36 km² | Visão municipal |
| **7** | ~5 km² | Visão de bairro (análise detalhada) |

**Decisão**: Armazenar H3 res 5, 6 e 7 para cada entrega. Mapa usa res 6 como padrão; zoom in→7, zoom out→5.

### Banco de Dados

**Supabase Pro** ($25/mês): PostgreSQL 16 + PostGIS (queries geoespaciais) + pgvector (embeddings RAG). 8GB storage suficiente para 800k linhas + agregados H3 + embeddings.

### Integrações Externas

| Serviço | Status API | Abordagem |
|---|---|---|
| **WorldPop** | API REST gratuita | Proxy Next.js → `/api/population` |
| **Correios** | API oficial (Bearer token, "Meu Correios") | Client autenticado |
| **Clique Retire** | API pública e-BOX (token necessário) | Client + GitBook docs |
| **ViaCEP** | API pública gratuita, sem auth | Client direto |

### RAG vs Text-to-SQL para 800k Linhas

RAG puro não é ideal para dados tabulares estruturados. A arquitetura correta é **híbrida**:

| Tipo de Query | Tecnologia | Exemplo |
|---|---|---|
| Métricas exatas | **Text-to-SQL** (LLM → PostGIS) | "Top 10 CEPs por volume de entregas" |
| Análise semântica | **RAG** (pgvector) | "Quais áreas têm perfil similar ao bairro X?" |
| Sugestões e insights | **RAG** + contexto H3 | "Sugira 3 novos pontos baseado nos gaps" |
| Correlações | **SQL direto** + Recharts | Gráfico scatter população vs entregas |

**Embeddings**: Apenas os ~50k agregados H3 (não as 800k linhas brutas). Cada embedding = vetor de 256 dimensões (text-embedding-3-small com `dimensions=256`) representando: densidade de entregas, população, cobertura de pontos, bairro, cidade.

---

## Stack Técnico Definitivo

```
Framework:     Next.js 15 (App Router) + React 19
Linguagem:     TypeScript (strict mode)
Estilo:        Tailwind CSS v4 + shadcn/ui
Mapa:          MapLibre GL JS + react-map-gl v8 + Deck.gl
Tiles:         MapTiler (free tier)
Banco:         Supabase Pro — PostgreSQL 16 + PostGIS + pgvector
ORM:           Prisma 6
Estado:        Zustand + TanStack Query v5
AI/RAG:        Vercel AI SDK + Claude (Anthropic) + LangChain.js
Embeddings:    OpenAI text-embedding-3-small (256 dim)
Geocoding:     ViaCEP + geocodebr (batch script)
Indexação:     h3-js (Uber H3)
Geo utilities: Turf.js
Excel parsing: xlsx (SheetJS)
Charts:        Recharts
Deploy:        Vercel (frontend + API routes serverless)
```

### Estimativa de Custos Mensais (MVP)

| Item | Custo/mês |
|---|---|
| Vercel (Hobby/Pro) | $0–20 |
| Supabase Pro | $25 |
| MapTiler free tier | $0 |
| Anthropic Claude API (~500k tokens/mês) | ~$5–15 |
| OpenAI Embeddings (geração única) | ~$0.50 (geração única de 50k embeddings) |
| **Total estimado** | **$30–60/mês** |

---

## Arquitetura de Dados

### Schema Prisma / PostgreSQL

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Delivery {
  id          String   @id @default(cuid())
  address     String
  cep         String?  @db.VarChar(8)
  city        String?  @db.VarChar(100)
  state       String?  @db.VarChar(2)
  lat         Decimal? @db.Decimal(10, 8)
  lng         Decimal? @db.Decimal(11, 8)
  h3Res5      String?  @db.VarChar(15)
  h3Res6      String?  @db.VarChar(15)
  h3Res7      String?  @db.VarChar(15)
  quantity    Int      @default(1)
  period      String?  // "2025-01", "2025-02", etc.
  rawData     Json?    // dados originais do Excel
  createdAt   DateTime @default(now())

  @@index([h3Res6])
  @@index([cep])
  @@map("deliveries")
}

model DeliveryAggregate {
  h3Index           String    @id @db.VarChar(15)
  resolution        Int
  deliveryCount     Int       @default(0)
  uniqueAddresses   Int       @default(0)
  totalQuantity     Int       @default(0)
  centerLat         Decimal   @db.Decimal(10, 8)
  centerLng         Decimal   @db.Decimal(11, 8)
  populationDensity Decimal?
  // pgvector extension — adicionado via migration SQL raw
  // embedding        Unsupported("vector(256)")?
  updatedAt         DateTime  @updatedAt

  @@index([resolution])
  @@map("delivery_aggregates")
}

model PickupPoint {
  id         String   @id @default(cuid())
  name       String
  provider   String   // "correios" | "clique_retire" | "manual"
  externalId String?
  address    String?
  city       String?
  state      String?  @db.VarChar(2)
  lat        Decimal  @db.Decimal(10, 8)
  lng        Decimal  @db.Decimal(11, 8)
  h3Res7     String?  @db.VarChar(15)
  type       String   // "agency" | "locker" | "partner"
  metadata   Json?
  isActive   Boolean  @default(true)
  updatedAt  DateTime @updatedAt

  @@index([provider])
  @@index([state])
  @@map("pickup_points")
}

model PopulationCell {
  h3Index    String   @id @db.VarChar(15)
  resolution Int
  population Int
  year       Int
  centerLat  Decimal  @db.Decimal(10, 8)
  centerLng  Decimal  @db.Decimal(11, 8)
  updatedAt  DateTime @updatedAt

  @@index([resolution])
  @@map("population_cells")
}
```

---

## Estrutura de Pastas

```
mvp-maps/
├── src/
│   ├── app/
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx               # Shell: sidebar + topbar
│   │   │   ├── page.tsx                 # redirect → /map
│   │   │   ├── map/
│   │   │   │   └── page.tsx             # Mapa interativo principal
│   │   │   ├── analysis/
│   │   │   │   └── page.tsx             # Aba de análise por IA
│   │   │   └── data/
│   │   │       └── page.tsx             # Upload e gestão de dados
│   │   ├── api/
│   │   │   ├── population/
│   │   │   │   └── route.ts             # Proxy WorldPop API
│   │   │   ├── packages/
│   │   │   │   ├── route.ts             # GET agregados / stats
│   │   │   │   └── upload/
│   │   │   │       └── route.ts         # POST upload Excel
│   │   │   ├── pickup-points/
│   │   │   │   ├── route.ts             # GET pontos de retirada
│   │   │   │   └── sync/
│   │   │   │       └── route.ts         # POST sync Correios + Clique
│   │   │   └── ai/
│   │   │       ├── chat/
│   │   │       │   └── route.ts         # POST stream AI chat
│   │   │       └── analyze/
│   │   │           └── route.ts         # POST análise automática
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                          # shadcn/ui (Button, Card, etc.)
│   │   ├── map/
│   │   │   ├── MapContainer.tsx         # MapLibre + Deck.gl wrapper
│   │   │   ├── layers/
│   │   │   │   ├── DeliveryHeatmap.tsx  # Deck.gl HeatmapLayer
│   │   │   │   ├── PopulationLayer.tsx  # Deck.gl GeoJsonLayer
│   │   │   │   ├── PickupPointsLayer.tsx # ScatterplotLayer + raio
│   │   │   │   └── H3GridLayer.tsx      # H3HexagonLayer (opcional)
│   │   │   └── controls/
│   │   │       ├── LayerControl.tsx     # Toggle camadas
│   │   │       ├── RadiusSlider.tsx     # Controle de raio
│   │   │       └── ResolutionControl.tsx # H3 zoom level
│   │   ├── analysis/
│   │   │   ├── AIChat.tsx               # Chat com Claude (Vercel AI SDK)
│   │   │   ├── CorrelationChart.tsx     # Scatter: população vs entregas
│   │   │   ├── CoverageChart.tsx        # % entregas cobertas por raio
│   │   │   └── InsightsPanel.tsx        # Sugestões da IA
│   │   └── data/
│   │       ├── ExcelUpload.tsx          # Drag-and-drop upload
│   │       ├── ColumnMapper.tsx         # AI-assisted column mapping
│   │       └── IngestProgress.tsx       # Progress bar ingestão
│   ├── lib/
│   │   ├── db/
│   │   │   ├── client.ts                # Prisma + Supabase client
│   │   │   └── queries/
│   │   │       ├── deliveries.ts        # PostGIS queries
│   │   │       ├── pickupPoints.ts
│   │   │       └── population.ts
│   │   ├── ai/
│   │   │   ├── pipeline.ts              # RAG + Text-to-SQL pipeline
│   │   │   ├── tools.ts                 # Claude tool definitions
│   │   │   ├── embeddings.ts            # OpenAI embedding helpers
│   │   │   └── prompts.ts               # System prompts
│   │   ├── geo/
│   │   │   ├── h3.ts                    # H3 indexing utilities
│   │   │   ├── turf.ts                  # Spatial calculations
│   │   │   └── worldpop.ts              # WorldPop API client
│   │   ├── integrations/
│   │   │   ├── correios.ts              # Correios API client
│   │   │   ├── cliqueRetire.ts          # Clique Retire e-BOX client
│   │   │   └── viacep.ts                # ViaCEP client
│   │   └── parsers/
│   │       ├── excel.ts                 # xlsx parsing + schema detection
│   │       └── geocoder.ts              # Batch geocoding pipeline
│   ├── hooks/
│   │   ├── useMapLayers.ts
│   │   ├── useDeliveryData.ts
│   │   └── useAIAnalysis.ts
│   ├── stores/
│   │   ├── mapStore.ts                  # Zustand: viewport, layers, filters
│   │   └── dataStore.ts                 # Zustand: upload state, stats
│   └── types/
│       ├── map.ts
│       ├── delivery.ts
│       ├── pickup.ts
│       ├── population.ts
│       └── ai.ts
├── prisma/
│   ├── schema.prisma
│   └── migrations/
├── scripts/
│   └── geocode-batch.ts                 # Script geocoding 800k offline
├── thoughts/
│   └── shared/
│       └── plans/
├── public/
├── .env.local
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json                        # strict: true, path aliases
```

---

## O que NÃO Faremos no MVP

- Autenticação de usuários (sem login/auth)
- Roteamento de última milha (não é otimizador de rotas)
- Integração com ERP/TMS em tempo real (dados são batch/upload)
- Isócronas (tempo de caminhada) — fica para v2
- App mobile
- Previsão de demanda time-series — fica para v2

---

## Fase 0: Setup do Projeto

### Visão Geral
Inicializar o projeto com toda a infraestrutura base configurada e funcionando.

### Mudanças Necessárias

#### 1. Inicialização Next.js 15
```bash
npx create-next-app@latest mvp-maps \
  --typescript --tailwind --eslint --app \
  --src-dir --import-alias "@/*"
```

#### 2. `tsconfig.json` — strict mode + path aliases
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/types/*": ["./src/types/*"]
    }
  }
}
```

#### 3. Dependências principais
```bash
# Mapa
npm i maplibre-gl react-map-gl @deck.gl/react @deck.gl/layers @deck.gl/geo-layers

# Banco + ORM
npm i @prisma/client @supabase/supabase-js
npm i -D prisma

# AI
npm i ai @ai-sdk/anthropic @ai-sdk/openai langchain

# Geo
npm i h3-js @turf/turf

# Excel
npm i xlsx

# Estado / Data fetching
npm i zustand @tanstack/react-query

# Charts
npm i recharts

# shadcn/ui
npx shadcn@latest init
```

#### 4. `.env.local`
```env
DATABASE_URL=postgresql://...
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
NEXT_PUBLIC_MAPTILER_KEY=...
CORREIOS_TOKEN=...
CLIQUE_RETIRE_TOKEN=...
```

#### 5. Prisma init + migration inicial
```bash
npx prisma init
npx prisma migrate dev --name init
```

#### 6. PostGIS + pgvector via SQL migration
**Arquivo**: `prisma/migrations/000_extensions/migration.sql`
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Coluna vector nos agregados (não suportada pelo Prisma nativo)
ALTER TABLE delivery_aggregates
  ADD COLUMN IF NOT EXISTS embedding vector(256);

CREATE INDEX delivery_aggregates_embedding_idx
  ON delivery_aggregates USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

### Critérios de Sucesso

#### Verificação Automatizada:
- [x] `npm run build` sem erros TypeScript
- [x] `npm run lint` sem warnings
- [ ] `npx prisma migrate status` → "Database schema is up to date"
- [ ] `npx prisma db pull` retorna schema com `deliveries`, `delivery_aggregates`, `pickup_points`, `population_cells`
- [ ] Conexão Supabase OK: `npx prisma db execute --stdin <<< "SELECT 1"`

#### Verificação Manual:
- [ ] `npm run dev` sobe sem erros no console
- [ ] Página inicial abre no browser
- [ ] Supabase dashboard mostra 4 tabelas criadas com extensões PostGIS e vector ativas

---

## Fase 1: Fundação do Mapa

### Visão Geral
Implementar o mapa interativo base com MapLibre GL JS + Deck.gl, com layout de dashboard, controles de camadas e estado gerenciado pelo Zustand.

### Mudanças Necessárias

#### 1. `src/stores/mapStore.ts`
```typescript
import { create } from 'zustand'

interface MapState {
  viewport: { longitude: number; latitude: number; zoom: number }
  activeLayers: { heatmap: boolean; population: boolean; pickupPoints: boolean }
  pickupRadius: number // metros
  h3Resolution: 5 | 6 | 7
  setViewport: (v: Partial<MapState['viewport']>) => void
  toggleLayer: (layer: keyof MapState['activeLayers']) => void
  setPickupRadius: (r: number) => void
}
```

#### 2. `src/components/map/MapContainer.tsx`
- `DeckGL` sobre `Map` (react-map-gl com maplibre-gl)
- mapStyle: `https://api.maptiler.com/maps/streets/style.json?key=${MAPTILER_KEY}`
- Layers dinâmicos baseados no `mapStore`

#### 3. `src/app/(dashboard)/layout.tsx`
- Sidebar: navegação Map / Analysis / Data
- Header com filtros globais (estado, período)

#### 4. `src/components/map/controls/`
- `LayerControl.tsx`: toggles shadcn/ui Switch para cada camada
- `RadiusSlider.tsx`: shadcn/ui Slider (300m → 5000m)

### Critérios de Sucesso

#### Verificação Automatizada:
- [x] `npm run build` sem erros
- [x] Componente `MapContainer` renderiza sem erros de SSR (usar `dynamic(() => import(...), { ssr: false })`)

#### Verificação Manual:
- [ ] Mapa exibe tiles do MapTiler centrado no Sudeste do Brasil
- [ ] Sidebar com 3 itens de navegação funciona
- [ ] Toggle de camadas altera estado no Zustand (verificar com React DevTools)
- [ ] Slider de raio funciona (300m–5km)
- [ ] Mapa responde a pan/zoom sem lag

---

## Fase 2: Ingestão de Dados de Pacotes (Excel → DB)

### Visão Geral
Pipeline completo de upload de Excel (.xlsx com 800k linhas), AI-assisted column mapping, geocoding em batch e indexação H3. Interface com progresso em tempo real.

### Mudanças Necessárias

#### 1. `src/lib/parsers/excel.ts`
```typescript
import * as XLSX from 'xlsx'

export async function parseExcelFile(file: File): Promise<{
  headers: string[]
  sample: Record<string, unknown>[]  // primeiras 10 linhas
  totalRows: number
}>
```

#### 2. `src/lib/parsers/geocoder.ts`
Pipeline de geocoding em batch:
```typescript
// 1. Por CEP via ViaCEP (gratuito, ~80% dos casos)
// 2. Fallback: lat/lng já presentes no arquivo
// 3. Fallback: nominatim via API para casos sem CEP
export async function geocodeBatch(
  rows: RawDeliveryRow[],
  onProgress: (processed: number, total: number) => void
): Promise<GeocodedDelivery[]>
```

#### 3. `src/lib/geo/h3.ts`
```typescript
import { latLngToCell } from 'h3-js'

export function assignH3Indices(lat: number, lng: number) {
  return {
    h3Res5: latLngToCell(lat, lng, 5),
    h3Res6: latLngToCell(lat, lng, 6),
    h3Res7: latLngToCell(lat, lng, 7),
  }
}

export async function computeAggregates(
  prisma: PrismaClient
): Promise<void>
// Executa SQL: GROUP BY h3_res6, contagens, atualiza delivery_aggregates
```

#### 4. `src/app/api/packages/upload/route.ts`
- Recebe FormData com arquivo .xlsx
- Usa streaming para processar em chunks de 1000 linhas
- Server-Sent Events para progresso em tempo real
- Ao final, dispara `computeAggregates()`

#### 5. `src/components/data/ExcelUpload.tsx`
- Drag-and-drop com react-dropzone
- Mostra preview das primeiras linhas
- `ColumnMapper.tsx`: permite ao usuário confirmar/corrigir o mapeamento detectado pela AI

#### 6. `src/components/data/ColumnMapper.tsx`
- Chama `/api/ai/chat` com as headers + 5 linhas de amostra
- AI sugere: "coluna X = endereço, coluna Y = quantidade, coluna Z = data"
- Usuário confirma ou ajusta antes de processar

### Critérios de Sucesso

#### Verificação Automatizada:
- [ ] `parseExcelFile()` retorna headers e sample corretos para arquivo de teste (100 linhas)
- [ ] `geocodeBatch()` com 10 CEPs válidos retorna 10 coordenadas
- [ ] `computeAggregates()` popula tabela `delivery_aggregates` via `prisma.$executeRaw`
- [ ] API `/api/packages/upload` retorna 200 com arquivo de 1000 linhas

#### Verificação Manual:
- [ ] Upload de arquivo Excel real de teste (1000 linhas) completa sem erros
- [ ] Progresso exibido em tempo real na UI
- [ ] ColumnMapper sugere colunas corretas com AI
- [ ] Após ingestão, Supabase dashboard mostra linhas em `deliveries` e `delivery_aggregates`
- [ ] Heatmap no mapa exibe pontos de entrega nas áreas esperadas

---

## Fase 3: Dados Populacionais WorldPop

### Visão Geral
Integrar dados populacionais WorldPop para o Sudeste do Brasil, converter para H3 e sobrepor no mapa.

### Mudanças Necessárias

#### 1. `src/lib/geo/worldpop.ts`
```typescript
// WorldPop REST API
// GET https://api.worldpop.org/v1/services/stats
//   ?dataset=wpgppop&year=2020&geojson={sudeste_geojson}&key={key}
// Retorna: populacao por célula de 1km²

export async function fetchWorldPopRegion(
  geojson: GeoJSON.Polygon,
  year: number
): Promise<WorldPopCell[]>

export async function importToH3(cells: WorldPopCell[]): Promise<void>
// Converte células WorldPop para H3 res 6/7, salva em population_cells
```

#### 2. `src/app/api/population/route.ts`
- `GET /api/population?bbox=...&resolution=6`
- Retorna dados de `population_cells` filtrados por bounding box
- Cache com `next: { revalidate: 86400 }` (dados diários)

#### 3. Script de importação inicial
**Arquivo**: `scripts/import-worldpop.ts`
- Executar uma vez para importar WorldPop Sudeste → PostgreSQL
- `npx tsx scripts/import-worldpop.ts`

#### 4. `src/components/map/layers/PopulationLayer.tsx`
- Deck.gl `GeoJsonLayer` com `H3HexagonLayer`
- Cor baseada em densidade: branco → vermelho
- Opacidade controlada pelo `LayerControl`

### Critérios de Sucesso

#### Verificação Automatizada:
- [ ] Script `import-worldpop.ts` executa sem erros e popula `population_cells`
- [ ] `GET /api/population?bbox=-47,-24,-42,-20&resolution=6` retorna JSON válido
- [ ] `population_cells` tem dados para SP, RJ, MG, ES

#### Verificação Manual:
- [ ] Camada de população visível no mapa
- [ ] Áreas densas (centro de SP, RJ) aparecem com cor mais intensa
- [ ] Toggle da camada funciona
- [ ] Tooltip ao hover mostra "X hab/km²"

---

## Fase 4: Pontos de Retirada

### Visão Geral
Integrar Correios (API oficial) e Clique Retire (e-BOX API), visualizar no mapa com raio configurável, e permitir entrada manual adicional.

### Mudanças Necessárias

#### 1. `src/lib/integrations/correios.ts`
```typescript
// POST https://cws.correios.com.br/token → Bearer token
// GET https://api.correios.com.br/v1/unidades?pagina=1&tamanhoPagina=100
// Filtra por: uf=SP,RJ,MG,ES → type="agency"
export async function syncCorreiosAgencies(): Promise<PickupPoint[]>
```

#### 2. `src/lib/integrations/cliqueRetire.ts`
```typescript
// Abordagem 1 (preferida): API e-BOX oficial
// https://clique-retire.gitbook.io/ebox
// Requer Authorization: Bearer {CLIQUE_RETIRE_TOKEN}

// Abordagem 2 (fallback): Inspecionar requests do mapa público
// https://webview.cliqueretire.com.br/map/
// Abrir o DevTools Network → filtrar por /api ou /locations
// O webview provavelmente consome um endpoint REST com GeoJSON dos lockers
// → Identificar endpoint → replicar no client

export async function syncCliqueRetireLockers(): Promise<PickupPoint[]>
```

**Nota**: O mapa público em `https://webview.cliqueretire.com.br/map/` carrega as localizações de alguma API interna. Inspecionar os requests de rede (DevTools → Network) nessa URL é o caminho mais rápido para identificar o endpoint exato antes de solicitar acesso à API oficial.

#### 3. `src/app/api/pickup-points/sync/route.ts`
- `POST /api/pickup-points/sync`
- Chama ambas as funções em paralelo (`Promise.all`)
- Upsert no banco (por `externalId + provider`)
- Retorna contagem atualizada

#### 4. `src/components/map/layers/PickupPointsLayer.tsx`
- Deck.gl `ScatterplotLayer` para os pontos
- Ícones diferenciados: Correios (laranja), Clique Retire (azul), manual (verde)
- Raio de influência: `ScatterplotLayer` com `radiusScale` do slider
- Tooltip com nome, tipo e endereço

### Critérios de Sucesso

#### Verificação Automatizada:
- [ ] `syncCorreiosAgencies()` retorna array de agências com lat/lng válidos
- [ ] `syncCliqueRetireLockers()` retorna lockers com lat/lng
- [ ] `POST /api/pickup-points/sync` popula tabela `pickup_points`
- [ ] `GET /api/pickup-points?bbox=...` retorna JSON com pontos

#### Verificação Manual:
- [ ] Pontos de retirada aparecem no mapa nas localizações corretas
- [ ] Raio de influência visível ao redor de cada ponto
- [ ] Ícones diferenciados por provider
- [ ] Slider de raio (300m–5km) atualiza raio em tempo real
- [ ] Tooltip com informações do ponto ao hover

---

## Fase 5: Aba de Análise por IA

### Visão Geral
Interface de análise com chat AI (Claude), gráficos de correlação e painel de sugestões geradas automaticamente.

### Mudanças Necessárias

#### 1. `src/lib/ai/tools.ts`
Claude tools (function calling via Vercel AI SDK):
```typescript
// Tool: query_deliveries
// Params: { sql: string } — Claude gera SQL PostGIS seguro
// Retorna resultados do banco

// Tool: get_h3_context
// Params: { h3Index: string } — busca dados do H3 cell
// Retorna: população, entregas, pontos de retirada, vizinhos

// Tool: vector_search
// Params: { query: string, limit: number }
// Retorna H3 cells semanticamente similares via pgvector

// Tool: generate_chart_data
// Params: { type: "scatter" | "bar" | "heatmap", data: ... }
// Retorna dados formatados para Recharts
```

#### 2. `src/lib/ai/pipeline.ts`
```typescript
import { streamText } from 'ai'
import { anthropic } from '@ai-sdk/anthropic'

export const systemPrompt = `
Você é um analista de geoespacial especializado em logística last-mile no Brasil.
Você tem acesso a dados de:
- Entregas por endereço (${aggregateCount} células H3)
- Densidade populacional WorldPop 2020
- Pontos de retirada Correios e Clique Retire

Responda em português. Use dados precisos.
Quando sugerir novos pontos de retirada, baseie-se em:
- Alto volume de entregas (>50/mês por H3 res7)
- Alta densidade populacional (>3000 hab/km²)
- Raio >800m sem ponto de retirada existente
`
```

#### 3. `src/app/api/ai/chat/route.ts`
```typescript
// POST com streaming (Vercel AI SDK streamText)
// Suporta tool calls para SQL, vector search, charts
// IMPORTANTE: Sanitização do SQL gerado antes de executar
```

#### 4. `src/app/api/ai/analyze/route.ts`
- Análise automática ao carregar a aba
- Gera automaticamente: correlação pop vs entregas, top gaps, sugestões de novos pontos

#### 5. `src/components/analysis/CorrelationChart.tsx`
```typescript
// Recharts ScatterChart
// X: população da célula H3 (WorldPop)
// Y: entregas por célula H3
// Color: cobertura por pontos de retirada (verde=coberto, vermelho=gap)
```

#### 6. `src/components/analysis/AIChat.tsx`
- Interface de chat (useChat do Vercel AI SDK)
- Suporte a renderização de gráficos inline nas respostas
- Histórico de conversa preservado no Zustand

### Critérios de Sucesso

#### Verificação Automatizada:
- [ ] `POST /api/ai/chat` retorna stream válido
- [ ] Tool `query_deliveries` executa SQL e retorna resultado sem SQL injection
- [ ] `POST /api/ai/analyze` retorna JSON com `correlation`, `gaps`, `suggestions`
- [ ] Testes de sanitização SQL passam

#### Verificação Manual:
- [ ] Chat responde perguntas como "Quais bairros de SP têm mais entregas?" com dados reais
- [ ] Gráfico de correlação gerado automaticamente ao carregar aba
- [ ] Claude sugere pelo menos 3 novos pontos de retirada com justificativa
- [ ] Sugestões são geoespacialmente coerentes (verificar no mapa)
- [ ] Respostas em português e com dados precisos

---

## Fase 6: MCP Server + Otimizações Avançadas

### Visão Geral
Criar um servidor MCP (Model Context Protocol) para que Claude Code e outros agentes possam consultar diretamente os dados do projeto. Adicionar clustering geoespacial para sugestão automática de novos pontos.

### Mudanças Necessárias

#### 1. `src/mcp/server.ts` — MCP Server
```typescript
// Ferramentas MCP expostas:
// - query_deliveries(sql): executa query PostGIS
// - get_population(h3_index): retorna densidade
// - find_coverage_gaps(radius_m, state): retorna H3 cells sem cobertura
// - suggest_pickup_points(n): retorna top-n sugestões por DBSCAN
```

#### 2. Algoritmo de Clustering (DBSCAN simplificado via SQL)
```sql
-- Identifica clusters de alta demanda sem cobertura de pontos de retirada
-- Usa PostGIS ST_ClusterDBSCAN
SELECT
  ST_ClusterDBSCAN(location, eps := 0.005, minpoints := 5)
    OVER () AS cluster_id,
  *
FROM delivery_aggregates
WHERE h3_index NOT IN (
  SELECT h3_res7 FROM pickup_points WHERE is_active = TRUE
)
AND delivery_count > 30
```

#### 3. Análise de Cobertura
```sql
-- % de entregas cobertas por pontos existentes
-- Para cada H3 res7, verifica se existe ponto de retirada a ≤ X metros
SELECT
  COUNT(*) FILTER (WHERE covered) * 100.0 / COUNT(*) AS coverage_pct
FROM (
  SELECT
    d.h3_index,
    EXISTS (
      SELECT 1 FROM pickup_points p
      WHERE ST_DWithin(
        ST_SetSRID(ST_Point(d.center_lng, d.center_lat), 4326)::geography,
        ST_SetSRID(ST_Point(p.lng, p.lat), 4326)::geography,
        800  -- 800 metros
      )
    ) AS covered
  FROM delivery_aggregates d
  WHERE resolution = 7
) subq
```

### Critérios de Sucesso

#### Verificação Automatizada:
- [ ] MCP server inicia sem erros: `node src/mcp/server.js`
- [ ] Tool `find_coverage_gaps` retorna H3 cells válidas
- [ ] Query DBSCAN executa em <5s para 50k agregados

#### Verificação Manual:
- [ ] Claude Code consegue consultar dados via MCP (`/mcp query_deliveries "SELECT COUNT(*) FROM deliveries"`)
- [ ] `suggest_pickup_points(5)` retorna 5 localizações geoespacialmente coerentes
- [ ] Pontos sugeridos aparecem no mapa como layer destacado
- [ ] Métrica de cobertura exibida no dashboard (ex: "67% das entregas cobertas em 800m")

---

## Sugestões de Modernização (v2+)

### 1. Isócronas (Tempo Real de Deslocamento)
Em vez de raio circular (simplista), calcular polígonos de isócrona — área acessível em X minutos a pé/bike.
- **Tecnologia**: Valhalla (open-source, self-hosted no Render) ou OpenRouteService API (free tier)
- **Impacto**: Análise realista em áreas com rios, rodovias, morros (como SP e RJ)

### 2. Scraping de Lockers Adicionais (Playwright)
Para redes sem API pública (Loggi, outros):
```typescript
// scripts/scrape-lockers.ts
// Playwright headless scraping do finder de lockers
// Exporta para JSON → importa na tabela pickup_points
```

### 3. Integração Futura com VTEX/Shopify
Para receber dados de pacotes em tempo real via webhook, eliminando o upload manual.
- Endpoint: `POST /api/webhooks/orders` → geocoding on-the-fly → atualização H3

### 4. Previsão de Demanda (Time-Series)
Com acumulação de dados históricos mensais:
- **Prophet (Meta)** via Python microservice
- Previsão de demanda por H3 cell para os próximos 3-6 meses
- Identificação precoce de áreas em crescimento antes de saturar

### 5. Score de Potencial por Local
Combinação de métricas em score normalizado (0-100):
```
Score = 0.35 × (entregas_sem_cobertura)
      + 0.30 × (densidade_pop)
      + 0.20 × (crescimento_tendência)
      + 0.15 × (ausência_concorrentes)
```

### 6. Relatório PDF Exportável
- Vercel AI SDK → Claude gera análise narrativa
- `@react-pdf/renderer` para PDF com mapas e gráficos
- Ideal para apresentações executivas

---

## Referências e Documentação

- WorldPop API: `https://api.worldpop.org/v1/services`
- Correios Developers: `https://www.correios.com.br/atendimento/developers`
- Clique Retire e-BOX: `https://clique-retire.gitbook.io/ebox`
- ViaCEP: `https://viacep.com.br/`
- Deck.gl: `https://deck.gl/docs`
- MapLibre GL JS: `https://maplibre.org/maplibre-gl-js/docs/`
- H3 docs: `https://h3geo.org/docs`
- Vercel AI SDK: `https://ai-sdk.dev/docs`
- geocodebr (IPEA): `https://ipeagit.github.io/geocodebr/`
