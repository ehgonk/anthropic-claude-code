"""
Ingest COTAHIST data into SQLite database

This script:
1. Scans data/b3_cotahist/ for COTAHIST files
2. Parses each file using CotahistParser
3. Creates/updates Stock records
4. Inserts StockPrice records in batches
5. Handles duplicates gracefully
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, insert, func
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.database import engine, Base
from app.models import Stock, StockPrice
from app.parsers import CotahistParser
from app.config import settings


async def create_tables():
    """Create database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables created")


async def get_or_create_stocks(conn, trading_codes: dict[str, str]) -> dict[str, int]:
    """
    Get or create Stock records for trading codes

    Args:
        conn: Database connection
        trading_codes: Dict of {trading_code: short_name}

    Returns:
        Dict of {trading_code: stock_id}
    """
    # Get existing stocks
    result = await conn.execute(
        select(Stock.id, Stock.symbol).where(Stock.symbol.in_(trading_codes.keys()))
    )
    existing = {row.symbol: row.id for row in result}

    # Create missing stocks
    new_stocks = []
    for code, name in trading_codes.items():
        if code not in existing:
            new_stocks.append({
                "symbol": code,
                "name": name,
                "price": 0.0,
                "change_percent": 0.0,
                "volume": 0,
                "updated_at": datetime.utcnow()
            })

    if new_stocks:
        # Insert new stocks
        stmt = insert(Stock).values(new_stocks)
        await conn.execute(stmt)

        # Get IDs of newly created stocks
        result = await conn.execute(
            select(Stock.id, Stock.symbol).where(Stock.symbol.in_(trading_codes.keys()))
        )
        existing = {row.symbol: row.id for row in result}

    return existing


async def insert_prices_batch(conn, prices: list[dict], batch_size: int = 1000):
    """
    Insert stock prices in batches using UPSERT (INSERT OR IGNORE)

    Args:
        conn: Database connection
        prices: List of price dictionaries
        batch_size: Number of records per batch
    """
    from sqlalchemy import delete

    total = len(prices)
    inserted = 0

    for i in range(0, total, batch_size):
        batch = prices[i:i + batch_size]

        # For SQLite, we'll use a simpler approach:
        # Delete existing records for this stock_id/date, then insert
        for price in batch:
            # Delete existing record if it exists
            stmt = delete(StockPrice).where(
                (StockPrice.stock_id == price['stock_id']) &
                (StockPrice.date == price['date'])
            )
            await conn.execute(stmt)

        # Insert new records
        stmt = insert(StockPrice).values(batch)
        await conn.execute(stmt)
        inserted += len(batch)

        if inserted % 10000 == 0:
            print(f"  Inserted {inserted:,}/{total:,} prices...")

    return inserted


async def ingest_file(file_path: Path, conn):
    """
    Ingest a single COTAHIST file

    Args:
        file_path: Path to COTAHIST file
        conn: Database connection
    """
    print(f"\n📂 Processing: {file_path.name}")

    parser = CotahistParser(file_path)

    # First pass: collect all trading codes
    print("  Step 1/3: Scanning trading codes...")
    trading_codes = {}  # {code: name}
    quotes_by_code = defaultdict(list)

    for quote in parser.parse():
        if quote.trading_code not in trading_codes:
            trading_codes[quote.trading_code] = quote.short_name
        quotes_by_code[quote.trading_code].append(quote)

    print(f"  Found {len(trading_codes)} unique stocks, {sum(len(q) for q in quotes_by_code.values()):,} quotes")

    # Step 2: Get or create Stock records
    print("  Step 2/3: Creating stock records...")
    stock_ids = await get_or_create_stocks(conn, trading_codes)
    print(f"  ✓ {len(stock_ids)} stocks ready")

    # Step 3: Prepare price records
    print("  Step 3/3: Inserting prices...")
    prices = []

    for code, quotes in quotes_by_code.items():
        stock_id = stock_ids.get(code)
        if not stock_id:
            continue

        for quote in quotes:
            prices.append({
                "stock_id": stock_id,
                "date": quote.date,
                "open": quote.open_price,
                "high": quote.high_price,
                "low": quote.low_price,
                "close": quote.close_price,
                "volume": quote.volume
            })

    # Insert in batches
    inserted = await insert_prices_batch(conn, prices)
    await conn.commit()
    print(f"  ✓ Inserted {inserted:,} price records")


async def ingest_all():
    """Ingest all COTAHIST files from data directory"""
    cotahist_dir = settings.data_dir / "b3_cotahist"

    if not cotahist_dir.exists():
        print(f"❌ Directory not found: {cotahist_dir}")
        return

    # Find all COTAHIST files
    files = sorted(cotahist_dir.glob("COTAHIST_A*.txt"))

    if not files:
        print(f"❌ No COTAHIST files found in {cotahist_dir}")
        return

    print(f"🚀 Found {len(files)} COTAHIST files")
    print(f"📊 Database: {settings.database_url}")

    # Create tables
    await create_tables()

    # Process files
    start_time = datetime.now()

    async with engine.begin() as conn:
        for file_path in files:
            try:
                await ingest_file(file_path, conn)
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                continue

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n✅ Ingestion completed in {elapsed:.1f}s")

    # Print statistics
    async with engine.begin() as conn:
        result = await conn.execute(select(func.count()).select_from(Stock))
        stock_count = result.scalar()

        result = await conn.execute(select(func.count()).select_from(StockPrice))
        price_count = result.scalar()

        print(f"\n📊 Database Statistics:")
        print(f"   Stocks: {stock_count:,}")
        print(f"   Price records: {price_count:,}")


async def main():
    """Main entry point"""
    try:
        await ingest_all()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
