"""
Seed database with real Yahoo Finance data

This script downloads stock data from Yahoo Finance (official free API)
and populates the database with real stock prices from the Brazilian stock exchange.

Data source: Yahoo Finance API (https://finance.yahoo.com)
Brazilian stocks use .SA suffix (e.g., PETR4.SA)
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from .database import AsyncSessionLocal, init_db
from .models import Stock, StockPrice
from .services.yahoo_finance_service import yahoo_finance_service


# Top B3 stocks by market cap and liquidity
TARGET_STOCKS = [
    "PETR4",  # Petrobras PN
    "VALE3",  # Vale ON
    "ITUB4",  # Itaú Unibanco PN
    "BBDC4",  # Bradesco PN
    "ABEV3",  # Ambev ON
    "MGLU3",  # Magazine Luiza ON
    "B3SA3",  # B3 S.A. ON
    "WEGE3",  # WEG ON
    "RENT3",  # Localiza ON
    "BBAS3",  # Banco do Brasil ON
    "SUZB3",  # Suzano ON
    "ELET3",  # Eletrobras ON
    "VIVT3",  # Telefônica Brasil ON
    "PRIO3",  # Prio ON
    "COGN3",  # Cogna Educação
]


async def seed_with_yahoo_finance(days: int = 365):
    """
    Seed database with real Yahoo Finance data

    Args:
        days: Number of days of historical data to download (default: 365)
    """
    print(f"=== Seeding Broker Database with Yahoo Finance ===\n")

    print("Initializing database...")
    await init_db()

    print(f"Downloading data for last {days} days from Yahoo Finance...")
    print(f"Target stocks: {', '.join(TARGET_STOCKS)}\n")

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Download stock data from Yahoo Finance
        stock_records = await yahoo_finance_service.fetch_stock_data(
            symbols=TARGET_STOCKS,
            start_date=start_date,
            end_date=end_date
        )

        if not stock_records:
            print("❌ No data available. Cannot seed database.")
            return

        print(f"Found {len(stock_records)} stocks with data\n")

        # Populate database
        async with AsyncSessionLocal() as db:
            for symbol, stock_data in stock_records.items():
                print(f"Processing {symbol} - {stock_data['name']}...")

                # Check if stock exists
                result = await db.execute(select(Stock).where(Stock.symbol == symbol))
                stock = result.scalar_one_or_none()

                if not stock:
                    # Create new stock
                    stock = Stock(
                        symbol=symbol,
                        name=stock_data['name'],
                        price=stock_data['price'],
                        change_percent=stock_data['change_percent'],
                        volume=stock_data['volume'],
                        updated_at=datetime.utcnow()
                    )
                    db.add(stock)
                    await db.flush()
                else:
                    # Update existing stock
                    stock.name = stock_data['name']
                    stock.price = stock_data['price']
                    stock.change_percent = stock_data['change_percent']
                    stock.volume = stock_data['volume']
                    stock.updated_at = datetime.utcnow()

                # Delete old prices
                await db.execute(
                    delete(StockPrice).where(StockPrice.stock_id == stock.id)
                )

                # Add historical prices
                print(f"  Adding {len(stock_data['prices'])} price records...")
                for price_data in stock_data['prices']:
                    stock_price = StockPrice(
                        stock_id=stock.id,
                        date=price_data['date'],
                        open=price_data['open'],
                        high=price_data['high'],
                        low=price_data['low'],
                        close=price_data['close'],
                        volume=price_data['volume'],
                    )
                    db.add(stock_price)

                await db.commit()
                print(f"  ✅ {symbol} completed\n")

        print("=" * 60)
        print("✅ Database seeded successfully with Yahoo Finance data!")
        print(f"   Period: {start_date.date()} to {end_date.date()}")
        print(f"   Stocks: {len(stock_records)}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        raise


async def seed_database():
    """Main seed function - uses real Yahoo Finance data"""
    await seed_with_yahoo_finance()


if __name__ == "__main__":
    asyncio.run(seed_database())
