from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Stock, StockPrice

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
