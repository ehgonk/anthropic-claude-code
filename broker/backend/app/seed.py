import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from .database import AsyncSessionLocal, init_db
from .models import Stock, StockPrice


# Top B3 stocks with mock data
MOCK_STOCKS = [
    {"symbol": "COGN3", "name": "Cogna Educação S.A.", "price": 2.45, "change_percent": -1.2},
    {"symbol": "PETR4", "name": "Petrobras PN", "price": 38.75, "change_percent": 2.3},
    {"symbol": "VALE3", "name": "Vale ON", "price": 62.18, "change_percent": 1.5},
    {"symbol": "ITUB4", "name": "Itaú Unibanco PN", "price": 28.92, "change_percent": 0.8},
    {"symbol": "BBDC4", "name": "Bradesco PN", "price": 13.45, "change_percent": -0.5},
    {"symbol": "ABEV3", "name": "Ambev ON", "price": 11.23, "change_percent": 1.1},
    {"symbol": "MGLU3", "name": "Magazine Luiza ON", "price": 4.67, "change_percent": -2.8},
    {"symbol": "B3SA3", "name": "B3 S.A. ON", "price": 12.89, "change_percent": 0.3},
    {"symbol": "WEGE3", "name": "WEG ON", "price": 45.32, "change_percent": 1.9},
    {"symbol": "RENT3", "name": "Localiza ON", "price": 38.54, "change_percent": -0.7},
    {"symbol": "BBAS3", "name": "Banco do Brasil ON", "price": 27.83, "change_percent": 1.4},
    {"symbol": "SUZB3", "name": "Suzano ON", "price": 58.92, "change_percent": 2.1},
    {"symbol": "ELET3", "name": "Eletrobras ON", "price": 41.76, "change_percent": -1.5},
    {"symbol": "VIVT3", "name": "Telefônica Brasil ON", "price": 49.23, "change_percent": 0.6},
    {"symbol": "PRIO3", "name": "Prio ON", "price": 52.14, "change_percent": 1.7},
]


def generate_historical_data(base_price: float, days: int = 365):
    """Generate realistic historical candlestick data"""
    data = []
    current_price = base_price * 0.85  # Start lower
    start_date = datetime.now() - timedelta(days=days)

    for i in range(days):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        # Random daily change between -3% and +3%
        change = random.uniform(-0.03, 0.03)
        current_price *= (1 + change)

        # Generate OHLC
        open_price = current_price
        close_price = current_price * (1 + random.uniform(-0.02, 0.02))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))

        # Generate volume (1M to 50M)
        volume = int(random.uniform(1000000, 50000000))

        data.append({
            "date": date_str,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume,
        })

    return data


async def seed_database():
    """Seed database with mock B3 stock data"""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        print(f"Seeding {len(MOCK_STOCKS)} stocks with mock data...")

        for stock_data in MOCK_STOCKS:
            symbol = stock_data["symbol"]
            print(f"Processing {symbol}...")

            # Check if stock already exists
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()

            # Generate random volume
            volume = int(random.uniform(5000000, 100000000))

            if not stock:
                # Create new stock
                stock = Stock(
                    symbol=symbol,
                    name=stock_data["name"],
                    price=stock_data["price"],
                    change_percent=stock_data["change_percent"],
                    volume=volume,
                    updated_at=datetime.utcnow()
                )
                db.add(stock)
                await db.flush()
            else:
                # Update existing stock
                stock.name = stock_data["name"]
                stock.price = stock_data["price"]
                stock.change_percent = stock_data["change_percent"]
                stock.volume = volume
                stock.updated_at = datetime.utcnow()

            # Generate historical data (last 365 days)
            print(f"  Generating historical data for {symbol}...")
            historical = generate_historical_data(stock_data["price"], days=365)

            # Delete old prices
            await db.execute(
                delete(StockPrice).where(StockPrice.stock_id == stock.id)
            )

            # Add new prices
            for hist in historical:
                stock_price = StockPrice(
                    stock_id=stock.id,
                    date=hist["date"],
                    open=hist["open"],
                    high=hist["high"],
                    low=hist["low"],
                    close=hist["close"],
                    volume=hist["volume"],
                )
                db.add(stock_price)

            print(f"  Added {len(historical)} price records for {symbol}")

            # Commit after each stock
            await db.commit()

        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
