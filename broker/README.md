# Broker - B3 Stock Market Visualization Platform

A modern stock market visualization platform for B3 (Brazilian Stock Exchange) with real-time charts and historical data.

## Features

- 📈 Interactive candlestick charts with volume
- 📊 Real-time stock quotes and price changes
- 🎨 Dark theme interface (TradingView-style)
- 📅 12-month historical data
- 🔍 Stock search and filtering

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Charts**: Lightweight Charts (TradingView)
- **Backend**: Python + FastAPI
- **Data Source**: B3 Bovespa API (brapi.dev)
- **Styling**: TailwindCSS

## Quick Start

```bash
# Install dependencies
make setup

# Load demo data
make seed

# Start backend (terminal 1)
make backend

# Start frontend (terminal 2)
make frontend
```

Visit http://localhost:5173

## Development

- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:5173
- API documentation at http://localhost:8000/docs

## Data Source

Historical stock data from B3 (Brazilian Stock Exchange) via brapi.dev API.
