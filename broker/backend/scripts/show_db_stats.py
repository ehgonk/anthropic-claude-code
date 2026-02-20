"""Show database statistics"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, text
from app.database import engine
from app.models import Stock, StockPrice


async def show_stats():
    """Show database statistics"""
    async with engine.connect() as conn:
        # Show stocks
        print("📊 Stocks in database:")
        result = await conn.execute(text("SELECT id, symbol, name FROM stocks"))
        for row in result:
            print(f"  [{row[0]}] {row[1]:10s} - {row[2]}")

        # Show price count per stock
        print("\n💰 Price records per stock:")
        result = await conn.execute(text("""
            SELECT s.symbol, COUNT(p.id) as count, MIN(p.date) as first_date, MAX(p.date) as last_date
            FROM stocks s
            LEFT JOIN stock_prices p ON s.id = p.stock_id
            GROUP BY s.id, s.symbol
            ORDER BY s.symbol
        """))
        for row in result:
            print(f"  {row[0]:10s}: {row[1]:3d} records | {row[2]} → {row[3]}")

        # Show sample prices
        print("\n📈 Sample price records:")
        result = await conn.execute(text("""
            SELECT s.symbol, p.date, p.open, p.high, p.low, p.close, p.volume
            FROM stock_prices p
            JOIN stocks s ON p.stock_id = s.id
            ORDER BY p.date DESC, s.symbol
            LIMIT 10
        """))
        for row in result:
            symbol, date, o, h, l, c, v = row
            print(f"  {symbol:10s} {date} | O:{o:10.2f} H:{h:10.2f} L:{l:10.2f} C:{c:10.2f} Vol:{v:12,d}")


if __name__ == "__main__":
    asyncio.run(show_stats())
