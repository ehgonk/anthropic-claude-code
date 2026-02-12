# Radar Insider — Análise de Insider Trading B3

Plataforma de análise de mercado brasileiro focada em insider trading lícito.
Cruza dados de negociações de administradores (CVM) com cotações (B3) para gerar
um score de tendência por ativo de -100 a +100.

## Stack

- **Backend:** Python 3.12+ / FastAPI / SQLAlchemy / SQLite (async)
- **Frontend:** React 18 / TypeScript / Vite / TailwindCSS / Recharts
- **Dados:** CVM (VLMO) + B3 (COTAHIST) — fontes públicas e gratuitas

## Estrutura

```
├── backend/              # API + ingestão + scoring
│   ├── app/
│   │   ├── api/          # Endpoints REST (FastAPI)
│   │   ├── models/       # SQLAlchemy models (Company, StockPrice, InsiderTrade, Score)
│   │   ├── services/     # Engine de scoring
│   │   ├── ingest/       # Scripts de ingestão CVM/B3
│   │   ├── config.py     # Configuração central
│   │   ├── database.py   # Setup SQLAlchemy async
│   │   ├── main.py       # Entrypoint FastAPI
│   │   └── seed.py       # Dados de demonstração
│   └── requirements.txt
├── frontend/             # Dashboard React
│   ├── src/
│   │   ├── components/   # ScoreGauge, PriceChart, RankingTable, etc.
│   │   ├── pages/        # Home, Ranking, Explorer, Admin
│   │   ├── hooks/        # useApi hook
│   │   └── services/     # API client
│   └── package.json
└── data/                 # Dados brutos (não versionados)
```

## Setup Rápido

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2. Dados de demonstração (para testar sem baixar da CVM/B3)

```bash
cd backend
python -m app.seed
```

### 3. Rodar o backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:5173

## Usando dados reais

Via painel Admin no frontend (http://localhost:5173/admin) ou via API:

```bash
# Ingestão CVM (insider trades)
curl -X POST http://localhost:8000/api/ingest/cvm/2024
curl -X POST http://localhost:8000/api/ingest/cvm/2025

# Ingestão B3 (cotações COTAHIST)
curl -X POST http://localhost:8000/api/ingest/b3/2024

# Recalcular scores
curl -X POST http://localhost:8000/api/scores/recalculate
```

## Como funciona o Score

O score de -100 a +100 é composto por 4 componentes:

| Componente        | Peso | O que mede                                    |
|-------------------|------|-----------------------------------------------|
| Insider Trading   | 40%  | Compras vs vendas de insiders (30d)            |
| Short Interest    | 20%  | Variação do short interest (30d)               |
| Fluxo Estrangeiro | 20%  | Fluxo líquido de investidores estrangeiros     |
| Momentum Técnico  | 20%  | Preço vs médias móveis (MA20, MA50)            |

**Sinais:**
- **COMPRA** (score >= +30): Atividade insider positiva + momentum favorável
- **NEUTRO** (-30 < score < +30): Sem sinal claro
- **VENDA** (score <= -30): Insiders vendendo + momentum negativo

**Bônus por anomalia:** Quando um insider que nunca comprou passa a comprar,
o score recebe bônus adicional (sinal de alta convicção).

## Páginas

- **Visão Geral**: Cards de resumo + ranking top 10 + trades recentes
- **Ranking**: Tabela completa ordenável com todos os scores
- **Explorer**: Gráfico de preço com overlay de trades de insiders + velocímetro do score
- **Admin**: Ingestão de dados e recálculo de scores

## API Endpoints

| Método | Endpoint                    | Descrição                              |
|--------|-----------------------------|----------------------------------------|
| GET    | /api/health                 | Health check                           |
| GET    | /api/companies              | Lista empresas (busca por ?search=)    |
| GET    | /api/prices/{ticker}        | Cotações históricas                    |
| GET    | /api/insider-trades         | Lista trades de insiders               |
| GET    | /api/scores/ranking         | Ranking por score                      |
| GET    | /api/scores/{ticker}        | Score atual de um ativo                |
| GET    | /api/scores/{ticker}/history| Histórico de scores                    |
| GET    | /api/dashboard/{ticker}     | Dados consolidados (preço+insider+score)|
| GET    | /api/summary                | Resumo geral                           |
| POST   | /api/ingest/cvm/{year}      | Ingere dados CVM de um ano             |
| POST   | /api/ingest/b3/{year}       | Ingere dados B3 de um ano              |
| POST   | /api/scores/recalculate     | Recalcula todos os scores              |

## Fontes de Dados

- **CVM VLMO**: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS
- **B3 COTAHIST**: https://bvmf.bmfbovespa.com.br/InstDados/SerHist

Todas as fontes são públicas e gratuitas. Nenhuma API paga necessária.
