"""
Seed database with real B3 COTAHIST data

This script downloads and parses B3 COTAHIST files (official historical stock data)
and populates the database with real stock prices from the Brazilian stock exchange.
"""

import asyncio
from datetime import datetime
from sqlalchemy import select, delete
from .database import AsyncSessionLocal, init_db
from .models import Stock, StockPrice
from .services.b3_cotahist import b3_service


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


async def seed_with_cotahist_data(year: int = None):
    """
    Seed database with real B3 COTAHIST data

    Args:
        year: Year to download data for (defaults to current year)
    """
    if year is None:
        year = datetime.now().year

    print(f"=== Seeding Broker Database with B3 COTAHIST {year} ===\n")

    print("Initializing database...")
    await init_db()

    print(f"Downloading COTAHIST data for {year}...")
    print(f"Target stocks: {', '.join(TARGET_STOCKS)}\n")

    try:
        # Download and parse COTAHIST data
        stock_data = await b3_service.get_stock_data(year, symbols=TARGET_STOCKS)

        if not stock_data:
            print(f"⚠️  No data found for year {year}")
            print("Falling back to previous year...")
            stock_data = await b3_service.get_stock_data(year - 1, symbols=TARGET_STOCKS)

        if not stock_data:
            print("❌ No data available. Cannot seed database.")
            return

        # Convert to stock records
        print("\nProcessing stock data...")
        stock_records = b3_service.df_to_stock_records(stock_data)

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
        print("✅ Database seeded successfully with real B3 COTAHIST data!")
        print(f"   Year: {year}")
        print(f"   Stocks: {len(stock_records)}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        raise


async def seed_database():
    """Main seed function - uses real COTAHIST data"""
    await seed_with_cotahist_data()


if __name__ == "__main__":
    asyncio.run(seed_database())
