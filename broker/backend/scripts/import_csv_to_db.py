"""
Import database from compressed CSV files

This imports:
- stocks.csv.gz
- stock_prices.csv.gz

Run this after pulling the CSV files from git.
"""

import sys
import gzip
import csv
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import insert, delete
from app.database import engine, Base
from app.models import Stock, StockPrice


async def import_from_csv():
    """Import database from compressed CSV files"""

    data_dir = Path(__file__).parent.parent.parent / "data" / "db_export"

    if not data_dir.exists():
        print(f"❌ Directory not found: {data_dir}")
        return

    stocks_file = data_dir / "stocks.csv.gz"
    prices_file = data_dir / "stock_prices.csv.gz"

    if not stocks_file.exists():
        print(f"❌ File not found: {stocks_file}")
        return

    if not prices_file.exists():
        print(f"❌ File not found: {prices_file}")
        return

    print("📊 Importing database from CSV...")
    print(f"📁 Source: {data_dir}")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables created")

    async with engine.begin() as conn:
        # Clear existing data
        print("\n🗑️  Clearing existing data...")
        await conn.execute(delete(StockPrice))
        await conn.execute(delete(Stock))

        # Import stocks
        print("\n1️⃣ Importing stocks...")
        with gzip.open(stocks_file, 'rt', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            stocks = []

            for row in reader:
                # Parse datetime string
                updated_at = row['updated_at']
                if updated_at and updated_at != 'None':
                    try:
                        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    except:
                        updated_at = datetime.utcnow()
                else:
                    updated_at = datetime.utcnow()

                stocks.append({
                    'id': int(row['id']),
                    'symbol': row['symbol'],
                    'name': row['name'],
                    'price': float(row['price']),
                    'change_percent': float(row['change_percent']),
                    'volume': int(row['volume']),
                    'updated_at': updated_at
                })

                if len(stocks) >= 1000:
                    await conn.execute(insert(Stock).values(stocks))
                    print(f"  Imported {len(stocks):,} stocks...")
                    stocks = []

            if stocks:
                await conn.execute(insert(Stock).values(stocks))

        print(f"✅ Stocks imported")

        # Import stock prices
        print("\n2️⃣ Importing stock prices...")
        with gzip.open(prices_file, 'rt', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            prices = []
            count = 0

            for row in reader:
                prices.append({
                    'id': int(row['id']),
                    'stock_id': int(row['stock_id']),
                    'date': row['date'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                })
                count += 1

                if len(prices) >= 10000:
                    await conn.execute(insert(StockPrice).values(prices))
                    print(f"  Imported {count:,} prices...")
                    prices = []

            if prices:
                await conn.execute(insert(StockPrice).values(prices))
                print(f"  Imported {count:,} prices...")

        print(f"✅ Stock prices imported")

    # Verify
    print("\n📊 Verifying import...")
    async with engine.connect() as conn:
        from sqlalchemy import func, text

        result = await conn.execute(text('SELECT COUNT(*) FROM stocks'))
        stock_count = result.scalar()

        result = await conn.execute(text('SELECT COUNT(*) FROM stock_prices'))
        price_count = result.scalar()

        print(f"\n✅ Import complete!")
        print(f"   Stocks: {stock_count:,}")
        print(f"   Prices: {price_count:,}")


if __name__ == "__main__":
    asyncio.run(import_from_csv())
