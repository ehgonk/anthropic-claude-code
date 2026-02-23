#!/usr/bin/env python3
"""
Populate database with mock data for testing
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import AsyncSessionLocal, init_db
from app.models import Stock, StockPrice
from sqlalchemy import select


# Real B3 stocks with realistic price ranges
MOCK_STOCKS = [
    {"symbol": "PETR4", "name": "PETROBRAS PN", "price": 36.50, "base_price": 35.00},
    {"symbol": "VALE3", "name": "VALE ON", "price": 58.60, "base_price": 55.00},
    {"symbol": "ITUB4", "name": "ITAU UNIBANCO PN", "price": 33.13, "base_price": 31.00},
    {"symbol": "BBDC4", "name": "BRADESCO PN", "price": 14.35, "base_price": 13.50},
    {"symbol": "ABEV3", "name": "AMBEV ON", "price": 12.85, "base_price": 12.00},
    {"symbol": "MGLU3", "name": "MAGAZINE LUIZA ON", "price": 8.45, "base_price": 8.00},
    {"symbol": "B3SA3", "name": "B3 ON", "price": 11.20, "base_price": 10.50},
    {"symbol": "WEGE3", "name": "WEG ON", "price": 45.30, "base_price": 43.00},
    {"symbol": "RENT3", "name": "LOCALIZA ON", "price": 52.10, "base_price": 50.00},
    {"symbol": "BBAS3", "name": "BANCO DO BRASIL ON", "price": 28.90, "base_price": 27.50},
]


def generate_historical_prices(base_price: float, days: int = 365) -> list:
    """Generate realistic historical price data"""
    prices = []
    current_price = base_price
    start_date = datetime.now() - timedelta(days=days)

    for day in range(days):
        date = start_date + timedelta(days=day)

        # Skip weekends
        if date.weekday() >= 5:
            continue

        # Generate daily price variation (-2% to +2%)
        variation = random.uniform(-0.02, 0.02)
        current_price *= (1 + variation)

        # Generate OHLC data
        open_price = current_price * random.uniform(0.98, 1.02)
        close_price = current_price * random.uniform(0.98, 1.02)
        high_price = max(open_price, close_price) * random.uniform(1.00, 1.03)
        low_price = min(open_price, close_price) * random.uniform(0.97, 1.00)

        # Generate volume (10M to 100M)
        volume = random.randint(10_000_000, 100_000_000)

        prices.append({
            'date': date.date(),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })

    return prices


async def populate_with_mock_data():
    """Populate database with mock data"""
    print("=" * 60)
    print("📊 Populating Database with Mock B3 Stock Data")
    print("=" * 60)
    print()

    # Initialize database
    print("🔧 Initializing database...")
    await init_db()
    print("✅ Database initialized")
    print()

    async with AsyncSessionLocal() as db:
        for stock_data in MOCK_STOCKS:
            symbol = stock_data['symbol']
            name = stock_data['name']
            current_price = stock_data['price']
            base_price = stock_data['base_price']

            print(f"📈 Processing {symbol} - {name}")

            # Check if stock exists
            result = await db.execute(
                select(Stock).where(Stock.symbol == symbol)
            )
            stock = result.scalar_one_or_none()

            if not stock:
                stock = Stock(
                    symbol=symbol,
                    name=name,
                    price=current_price,
                    change_percent=random.uniform(-3, 3),
                    volume=random.randint(10_000_000, 100_000_000),
                    updated_at=datetime.utcnow()
                )
                db.add(stock)
                await db.flush()
                print(f"   ✨ Created stock")
            else:
                print(f"   ♻️  Stock exists, updating...")
                stock.price = current_price
                stock.change_percent = random.uniform(-3, 3)
                stock.volume = random.randint(10_000_000, 100_000_000)
                stock.updated_at = datetime.utcnow()

            # Generate historical prices (1 year)
            print(f"   📊 Generating 1 year of historical data...")
            historical_prices = generate_historical_prices(base_price, days=365)

            # Add price data
            for price_data in historical_prices:
                # Check if price already exists
                result = await db.execute(
                    select(StockPrice).where(
                        StockPrice.stock_id == stock.id,
                        StockPrice.date == price_data['date']
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    stock_price = StockPrice(
                        stock_id=stock.id,
                        date=price_data['date'],
                        open=price_data['open'],
                        high=price_data['high'],
                        low=price_data['low'],
                        close=price_data['close'],
                        volume=price_data['volume']
                    )
                    db.add(stock_price)

            await db.commit()
            print(f"   ✅ Added {len(historical_prices)} price records")
            print()

    print("=" * 60)
    print("✅ Database populated successfully!")
    print(f"   Stocks: {len(MOCK_STOCKS)}")
    print(f"   Historical data: ~1 year per stock")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(populate_with_mock_data())
