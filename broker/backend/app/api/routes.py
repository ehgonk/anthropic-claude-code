from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
from ..database import get_db
from ..models import Stock, StockPrice
from ..services.b3_cotahist import b3_service
from ..seed import TARGET_STOCKS

router = APIRouter(prefix="/api")


@router.get("/stocks")
async def get_stocks(db: AsyncSession = Depends(get_db)):
    """Get all stocks"""
    result = await db.execute(select(Stock))
    stocks = result.scalars().all()

    return [
        {
            "symbol": stock.symbol,
            "name": stock.name,
            "price": stock.price,
            "change_percent": stock.change_percent,
            "volume": stock.volume,
        }
        for stock in stocks
    ]


@router.get("/stocks/{symbol}/candles")
async def get_candle_data(symbol: str, db: AsyncSession = Depends(get_db)):
    """Get candlestick data for a symbol"""
    # Get stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()

    if not stock:
        return []

    # Get prices ordered by date
    result = await db.execute(
        select(StockPrice)
        .where(StockPrice.stock_id == stock.id)
        .order_by(StockPrice.date)
    )
    prices = result.scalars().all()

    return [
        {
            "time": price.date,
            "open": price.open,
            "high": price.high,
            "low": price.low,
            "close": price.close,
            "volume": price.volume,
        }
        for price in prices
    ]


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@router.post("/ingest/b3/{year}")
async def ingest_b3_cotahist(year: int, db: AsyncSession = Depends(get_db)):
    """
    Ingest B3 COTAHIST data for a specific year

    Downloads and parses B3 COTAHIST files and updates the database
    with real historical stock data.

    Args:
        year: Year to download (e.g., 2024, 2025)

    Returns:
        Summary of ingestion (number of stocks and records processed)
    """
    try:
        # Validate year
        current_year = datetime.now().year
        if year < 2000 or year > current_year:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid year. Must be between 2000 and {current_year}"
            )

        # Download and parse COTAHIST data
        stock_data = await b3_service.get_stock_data(year, symbols=TARGET_STOCKS)

        if not stock_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for year {year}"
            )

        # Convert to stock records
        stock_records = b3_service.df_to_stock_records(stock_data)

        total_prices = 0

        # Update database
        for symbol, stock_data in stock_records.items():
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

            # Delete old prices for this year
            await db.execute(
                delete(StockPrice).where(StockPrice.stock_id == stock.id)
            )

            # Add new prices
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
                total_prices += 1

            await db.commit()

        return {
            "status": "success",
            "year": year,
            "stocks_processed": len(stock_records),
            "price_records": total_prices,
            "symbols": list(stock_records.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
