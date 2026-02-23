#!/usr/bin/env python3
"""
Populate database with existing COTAHIST data
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import AsyncSessionLocal, init_db
from app.models import Stock, StockPrice
from app.services.b3_cotahist import parse_cotahist_line
from sqlalchemy import select


TARGET_STOCKS = [
    "PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3",
    "MGLU3", "B3SA3", "WEGE3", "RENT3", "BBAS3"
]


async def populate_from_file(file_path: Path):
    """Populate database from COTAHIST text file"""
    print(f"📂 Reading file: {file_path}")

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    # Read and parse file
    stock_data = {}

    with open(file_path, 'r', encoding='latin1') as f:
        for line in f:
            parsed = parse_cotahist_line(line)
            if not parsed:
                continue

            ticker = parsed['ticker']

            # Filter only target stocks
            if ticker not in TARGET_STOCKS:
                continue

            if ticker not in stock_data:
                stock_data[ticker] = {
                    'name': parsed['name'],
                    'prices': []
                }

            stock_data[ticker]['prices'].append({
                'date': parsed['trade_date'],
                'open': parsed['open_price'],
                'high': parsed['high_price'],
                'low': parsed['low_price'],
                'close': parsed['close_price'],
                'volume': parsed['volume']
            })

    if not stock_data:
        print("⚠️  No target stocks found in file")
        return

    print(f"\n✅ Found {len(stock_data)} stocks with data")

    # Initialize database
    await init_db()

    # Populate database
    async with AsyncSessionLocal() as db:
        for ticker, data in stock_data.items():
            print(f"\n📊 Processing {ticker} - {data['name']}")

            # Get or create stock
            result = await db.execute(
                select(Stock).where(Stock.symbol == ticker)
            )
            stock = result.scalar_one_or_none()

            if not stock:
                # Get last price data
                last_price = data['prices'][-1] if data['prices'] else None

                stock = Stock(
                    symbol=ticker,
                    name=data['name'],
                    price=last_price['close'] if last_price else 0,
                    change_percent=0.0,
                    volume=last_price['volume'] if last_price else 0,
                    updated_at=datetime.utcnow()
                )
                db.add(stock)
                await db.flush()
                print(f"   ✨ Created stock: {ticker}")
            else:
                print(f"   ♻️  Stock exists: {ticker}")

            # Add price data
            for price_data in data['prices']:
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
            print(f"   ✅ Added {len(data['prices'])} price records")

    print("\n" + "="*60)
    print("✅ Database populated successfully!")
    print("="*60)


async def main():
    """Main function"""
    # Try multiple possible locations
    possible_paths = [
        Path("/home/user/anthropic-claude-code/broker/data/b3_cotahist/COTAHIST_A2024.txt"),
        Path("/home/user/anthropic-claude-code/broker/backend/data/b3_cotahist/COTAHIST_A2024.txt"),
        Path("data/b3_cotahist/COTAHIST_A2024.txt"),
    ]

    for file_path in possible_paths:
        if file_path.exists():
            await populate_from_file(file_path)
            return

    print("❌ No COTAHIST file found in expected locations")


if __name__ == "__main__":
    asyncio.run(main())
