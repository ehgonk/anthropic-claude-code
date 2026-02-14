# Broker - B3 Stock Market Visualization Platform

A modern stock market visualization platform for B3 (Brazilian Stock Exchange) with interactive charts and **real historical data from B3 COTAHIST**.

## Features

- 📈 Interactive candlestick charts with volume
- 📊 Real stock quotes and price changes
- 🎨 Dark theme interface (TradingView-style)
- 📅 Historical data from B3 COTAHIST (official source)
- 🔍 Stock search and filtering
- 🇧🇷 15 top Brazilian stocks (PETR4, VALE3, ITUB4, etc.)

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Charts**: Lightweight Charts (TradingView)
- **Backend**: Python + FastAPI
- **Data Source**: B3 COTAHIST (official historical data)
- **Styling**: TailwindCSS
- **Database**: SQLite (async)

## Quick Start

```bash
# Install dependencies
make setup

# Load real B3 COTAHIST data
make seed

# Start backend (terminal 1)
make backend

# Start frontend (terminal 2)
make frontend
```

Visit http://localhost:5174

## Development

- Backend runs on http://localhost:8001
- Frontend runs on http://localhost:5174
- API documentation at http://localhost:8001/docs

## Data Source

### B3 COTAHIST

This project uses **B3 COTAHIST** - the official historical stock data from the Brazilian Stock Exchange (B3).

- **Source**: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/
- **Format**: Fixed-width positional files (layout documented by B3)
- **Data**: Daily OHLC (Open, High, Low, Close) + Volume for all B3 stocks
- **Free**: Public data, no API keys required

### Stocks Available

The application tracks 15 top Brazilian stocks:

- **PETR4** - Petrobras PN
- **VALE3** - Vale ON
- **ITUB4** - Itaú Unibanco PN
- **BBDC4** - Bradesco PN
- **ABEV3** - Ambev ON
- **MGLU3** - Magazine Luiza ON
- **B3SA3** - B3 S.A. ON
- **WEGE3** - WEG ON
- **RENT3** - Localiza ON
- **BBAS3** - Banco do Brasil ON
- **SUZB3** - Suzano ON
- **ELET3** - Eletrobras ON
- **VIVT3** - Telefônica Brasil ON
- **PRIO3** - Prio ON
- **COGN3** - Cogna Educação

## API Endpoints

| Method | Endpoint                 | Description                          |
|--------|--------------------------|--------------------------------------|
| GET    | /api/health              | Health check                         |
| GET    | /api/stocks              | List all stocks                      |
| GET    | /api/stocks/{symbol}/candles | Get candlestick data for a stock |
| POST   | /api/ingest/b3/{year}    | Ingest B3 COTAHIST data for a year   |

## Ingesting Real Data

### Via Command Line

```bash
cd backend
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Seed with current year
python -m app.seed

# Or use a specific year
python -c "from app.seed import seed_with_cotahist_data; import asyncio; asyncio.run(seed_with_cotahist_data(2024))"
```

### Via API

```bash
# Ingest data for 2024
curl -X POST http://localhost:8001/api/ingest/b3/2024

# Ingest data for 2025
curl -X POST http://localhost:8001/api/ingest/b3/2025
```

## Architecture

```
broker/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # API endpoints
│   │   ├── models/
│   │   │   └── stock.py           # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── b3_cotahist.py     # B3 COTAHIST downloader/parser
│   │   │   └── brapi.py           # (legacy - not used)
│   │   ├── config.py              # Configuration
│   │   ├── database.py            # SQLAlchemy setup
│   │   ├── main.py                # FastAPI app
│   │   └── seed.py                # Database seeding
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── services/              # API client
│   │   └── App.tsx                # Main app
│   └── package.json
└── data/
    ├── broker.db                  # SQLite database
    └── cache/                     # COTAHIST cache files
```

## Performance

- **Data caching**: COTAHIST files are cached locally (Parquet format)
- **Fast parsing**: Uses `b3fileparser` library with Pandas
- **Async operations**: All I/O operations are async (database, HTTP)

## License

MIT License
