#!/usr/bin/env python3
"""Initialize database tables"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, engine
from app.models.stock import Stock, StockPrice  # Import models to register them


async def main():
    print("🗄️  Initializing database...")
    print(f"   Database: {engine.url}")

    try:
        await init_db()
        print("✅ Database tables created successfully!")
        print("   Tables: stocks, stock_prices")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
