#!/usr/bin/env python3
"""
Download complete B3 historical data (1986-2025)

This script downloads ALL available COTAHIST files from B3 and stores them in the database.
It generates a summary report of downloaded periods.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal, init_db
from app.services.b3_cotahist import b3_service
from app.models.stock import Stock, StockPrice
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


# B3 COTAHIST historical data available from 1986 to current year
START_YEAR = 1986
END_YEAR = datetime.now().year


async def save_to_database(session, stock_data: dict) -> dict:
    """
    Save parsed stock data to database

    Returns:
        Dictionary with statistics about the save operation
    """
    stats = {
        'stocks_added': 0,
        'stocks_updated': 0,
        'prices_added': 0,
        'periods': set(),  # Will store YYYY-MM periods
    }

    for symbol, data in stock_data.items():
        # Upsert stock
        stmt = sqlite_insert(Stock).values(
            symbol=symbol,
            name=data['name'],
            price=data['price'],
            change_percent=data['change_percent'],
            volume=data['volume'],
            updated_at=datetime.utcnow()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['symbol'],
            set_={
                'name': data['name'],
                'price': data['price'],
                'change_percent': data['change_percent'],
                'volume': data['volume'],
                'updated_at': datetime.utcnow()
            }
        )

        result = await session.execute(stmt)

        # Check if it was an insert or update
        if result.rowcount > 0:
            # Get the stock_id
            stock_result = await session.execute(
                select(Stock).where(Stock.symbol == symbol)
            )
            stock = stock_result.scalar_one()

            if stock.id == result.lastrowid:
                stats['stocks_added'] += 1
            else:
                stats['stocks_updated'] += 1

            # Insert prices (with upsert to avoid duplicates)
            for price_data in data['prices']:
                price_stmt = sqlite_insert(StockPrice).values(
                    stock_id=stock.id,
                    date=price_data['date'],
                    open=price_data['open'],
                    high=price_data['high'],
                    low=price_data['low'],
                    close=price_data['close'],
                    volume=price_data['volume']
                )
                # Use constraint name for upsert
                price_stmt = price_stmt.on_conflict_do_update(
                    constraint='uq_stock_date',
                    set_={
                        'open': price_data['open'],
                        'high': price_data['high'],
                        'low': price_data['low'],
                        'close': price_data['close'],
                        'volume': price_data['volume']
                    }
                )

                await session.execute(price_stmt)
                stats['prices_added'] += 1

                # Track period (YYYY-MM)
                period = price_data['date'][:7]  # Extract YYYY-MM
                stats['periods'].add(period)

    await session.commit()
    return stats


async def download_year(year: int) -> tuple[int, dict, str | None]:
    """
    Download and parse data for a specific year

    Returns:
        Tuple of (year, stock_data, error_message)
    """
    try:
        print(f"\n{'='*60}")
        print(f"📅 Processing year: {year}")
        print(f"{'='*60}")

        stock_data = await b3_service.get_stock_data(year)
        stock_records = b3_service.df_to_stock_records(stock_data)

        print(f"✅ Year {year}: {len(stock_records)} stocks processed")
        return (year, stock_records, None)

    except Exception as e:
        error_msg = f"❌ Error downloading year {year}: {str(e)}"
        print(error_msg)
        return (year, {}, error_msg)


async def main():
    """Main download orchestrator"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  B3 HISTORICAL DATA DOWNLOADER                               ║
║  Period: {START_YEAR} - {END_YEAR}                                      ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Initialize database
    print("🗄️  Initializing database...")
    await init_db()
    print("✅ Database initialized\n")

    # Track overall statistics
    overall_stats = {
        'total_stocks': 0,
        'total_prices': 0,
        'periods': set(),
        'years_success': [],
        'years_failed': [],
        'errors': []
    }

    # Download each year sequentially (to avoid overwhelming the server)
    async with AsyncSessionLocal() as session:
        for year in range(START_YEAR, END_YEAR + 1):
            year_num, stock_records, error = await download_year(year)

            if error:
                overall_stats['years_failed'].append(year_num)
                overall_stats['errors'].append(error)
                continue

            if not stock_records:
                print(f"⚠️  No data for year {year_num}")
                continue

            # Save to database
            print(f"💾 Saving {len(stock_records)} stocks to database...")
            save_stats = await save_to_database(session, stock_records)

            overall_stats['total_stocks'] += save_stats['stocks_added']
            overall_stats['total_prices'] += save_stats['prices_added']
            overall_stats['periods'].update(save_stats['periods'])
            overall_stats['years_success'].append(year_num)

            print(f"✅ Saved: {save_stats['stocks_added']} new stocks, "
                  f"{save_stats['stocks_updated']} updated stocks, "
                  f"{save_stats['prices_added']} price records")

    # Generate summary report
    print("\n\n")
    print(f"{'='*60}")
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"{'='*60}\n")

    print(f"✅ Years processed successfully: {len(overall_stats['years_success'])}")
    print(f"❌ Years failed: {len(overall_stats['years_failed'])}")
    print(f"📈 Total stocks: {overall_stats['total_stocks']}")
    print(f"💹 Total price records: {overall_stats['total_prices']}")

    if overall_stats['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in overall_stats['errors']:
            print(f"   - {error}")

    # Generate period table
    print(f"\n\n")
    print(f"{'='*60}")
    print(f"📅 PERIODS DOWNLOADED (YYYY-MM)")
    print(f"{'='*60}\n")

    if overall_stats['periods']:
        # Sort periods
        sorted_periods = sorted(overall_stats['periods'])

        # Group by year
        periods_by_year = defaultdict(list)
        for period in sorted_periods:
            year = period[:4]
            month = period[5:7]
            periods_by_year[year].append(month)

        # Print table
        print(f"{'Year':<8} {'Months':<50}")
        print(f"{'-'*60}")

        for year in sorted(periods_by_year.keys()):
            months = ', '.join(sorted(periods_by_year[year]))
            print(f"{year:<8} {months:<50}")

        print(f"\n📊 Total unique periods: {len(sorted_periods)}")
        print(f"📅 Date range: {sorted_periods[0]} to {sorted_periods[-1]}")
    else:
        print("⚠️  No periods downloaded")

    print("\n✅ Download complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
