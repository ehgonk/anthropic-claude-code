# Broker - B3 Stock Market Visualization Platform

A modern stock market visualization platform for B3 (Brazilian Stock Exchange) with interactive charts and **real historical data from Yahoo Finance**.

## Features

- 📈 Interactive candlestick charts with volume
- 📊 Real stock quotes and price changes
- 🎨 Dark theme interface (TradingView-style)
- 📅 Historical data from Yahoo Finance (free and reliable API)
- 🔍 Stock search and filtering
- 🇧🇷 15 top Brazilian stocks (PETR4, VALE3, ITUB4, etc.)

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Charts**: Lightweight Charts (TradingView)
- **Backend**: Python + FastAPI
- **Data Source**: Yahoo Finance API (official, free, and reliable)
- **Styling**: TailwindCSS
- **Database**: SQLite (async)

## Quick Start

```bash
# Install dependencies
make setup

# Load real data from Yahoo Finance
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

### Yahoo Finance API

This project uses **Yahoo Finance API** - a free and reliable source for historical stock data.

- **Source**: https://finance.yahoo.com
- **API**: Direct HTTP API calls (query1.finance.yahoo.com)
- **Data**: Daily OHLC (Open, High, Low, Close) + Volume for Brazilian stocks
- **Format**: Brazilian stocks use .SA suffix (e.g., PETR4.SA, VALE3.SA)
- **Historical Range**: Data available from 2000 onwards (26+ years)
- **Free**: No API keys required, no rate limits for reasonable usage

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

## Loading Real Data

### Via Command Line

```bash
cd backend
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Seed with Yahoo Finance data (last 365 days)
python -m app.seed
```

The seed command will:
- Download real historical data from Yahoo Finance
- Populate the database with 15 top Brazilian stocks
- Include 1 year of OHLCV data (configurable)

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
│   │   │   ├── yahoo_finance_service.py  # Yahoo Finance API client
│   │   │   └── auto_update.py     # Auto-update service
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
    └── cache/                     # Cache files
```

## Performance

- **Direct API access**: Uses httpx for direct Yahoo Finance API calls
- **No rate limits**: Reasonable usage without proxy issues
- **Async operations**: All I/O operations are async (database, HTTP)
- **Smart retry**: Automatic retry with exponential backoff for network issues

## License

MIT License
