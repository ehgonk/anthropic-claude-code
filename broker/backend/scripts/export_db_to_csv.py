"""
Export database to compressed CSV files

This exports:
- stocks.csv.gz
- stock_prices.csv.gz

These files can be committed to git and imported on another machine.
"""

import sys
import gzip
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import select, text
from app.database import engine
from app.models import Stock, StockPrice


async def export_to_csv():
    """Export database to compressed CSV files"""

    output_dir = Path(__file__).parent.parent.parent / "data" / "db_export"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("📊 Exporting database to CSV...")

    async with engine.connect() as conn:
        # Export stocks
        print("\n1️⃣ Exporting stocks...")
        result = await conn.execute(text("""
            SELECT id, symbol, name, price, change_percent, volume, updated_at
            FROM stocks
            ORDER BY symbol
        """))

        stocks_file = output_dir / "stocks.csv.gz"
        with gzip.open(stocks_file, 'wt', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'symbol', 'name', 'price', 'change_percent', 'volume', 'updated_at'])

            count = 0
            for row in result:
                writer.writerow(row)
                count += 1
                if count % 1000 == 0:
                    print(f"  Exported {count:,} stocks...")

        print(f"✅ Exported {count:,} stocks to {stocks_file}")

        # Export stock prices
        print("\n2️⃣ Exporting stock prices...")
        result = await conn.execute(text("""
            SELECT id, stock_id, date, open, high, low, close, volume
            FROM stock_prices
            ORDER BY stock_id, date
        """))

        prices_file = output_dir / "stock_prices.csv.gz"
        with gzip.open(prices_file, 'wt', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'stock_id', 'date', 'open', 'high', 'low', 'close', 'volume'])

            count = 0
            for row in result:
                writer.writerow(row)
                count += 1
                if count % 10000 == 0:
                    print(f"  Exported {count:,} prices...")

        print(f"✅ Exported {count:,} prices to {prices_file}")

    # Print summary
    print(f"\n📦 Export complete!")
    print(f"\n📁 Files created:")
    for file in [stocks_file, prices_file]:
        size_mb = file.stat().st_size / 1024 / 1024
        print(f"  {file.name:20s} {size_mb:8.2f} MB")

    print(f"\n✅ Files saved to: {output_dir}")
    print(f"\n📋 Next steps:")
    print(f"  1. git add data/db_export/*.csv.gz")
    print(f"  2. git commit -m 'Add B3 historical data (CSV export)'")
    print(f"  3. git push")


if __name__ == "__main__":
    asyncio.run(export_to_csv())
