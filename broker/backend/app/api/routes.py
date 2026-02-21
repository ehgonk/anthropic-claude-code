from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from datetime import datetime
from ..database import get_db
from ..models import Stock, StockPrice
from ..services.b3_cotahist import b3_service
from ..seed import TARGET_STOCKS

router = APIRouter(prefix="/api")


@router.get("/last-update")
async def get_last_update(db: AsyncSession = Depends(get_db)):
    """Get the date of the last downloaded B3 quote"""
    result = await db.execute(
        select(func.max(StockPrice.date))
    )
    last_date = result.scalar_one_or_none()

    result_min = await db.execute(
        select(func.min(StockPrice.date))
    )
    first_date = result_min.scalar_one_or_none()

    result_count = await db.execute(
        select(func.count(StockPrice.id))
    )
    total_records = result_count.scalar_one_or_none() or 0

    return {
        "last_date": last_date,
        "first_date": first_date,
        "total_records": total_records,
    }


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


# B3 COTAHIST endpoints disabled - Yahoo Finance is the single data source
# @router.post("/ingest/b3/range")
# @router.post("/ingest/b3/{year}")
