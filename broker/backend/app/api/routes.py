from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from datetime import datetime
from typing import Optional
from ..database import get_db
from ..models import Stock, StockPrice
from ..services.auto_update import auto_update_service
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


@router.post("/update/run")
async def run_update(
    force: bool = False,
    full_historical: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Trigger data update from Investing.com

    Args:
        force: Re-download existing data
        full_historical: Download ALL data from 1994 to now
    """
    try:
        result = await auto_update_service.run_update(
            force=force,
            full_historical=full_historical
        )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/update/status")
async def get_update_status():
    """Get current update status"""
    return auto_update_service.get_status()


@router.get("/data/stats")
async def get_data_stats(db: AsyncSession = Depends(get_db)):
    """Get detailed statistics about available data"""
    # Get year range
    result_min = await db.execute(select(func.min(StockPrice.date)))
    first_date = result_min.scalar_one_or_none()

    result_max = await db.execute(select(func.max(StockPrice.date)))
    last_date = result_max.scalar_one_or_none()

    # Get total records
    result_count = await db.execute(select(func.count(StockPrice.id)))
    total_records = result_count.scalar_one_or_none() or 0

    # Get records per year
    result_years = await db.execute(
        select(
            func.strftime('%Y', StockPrice.date).label('year'),
            func.count().label('count')
        ).group_by('year')
    )
    year_stats = [{"year": int(row.year), "count": row.count} for row in result_years]

    # Get unique stocks
    result_stocks = await db.execute(select(func.count(func.distinct(Stock.id))))
    total_stocks = result_stocks.scalar_one_or_none() or 0

    return {
        "first_date": first_date,
        "last_date": last_date,
        "total_records": total_records,
        "total_stocks": total_stocks,
        "years": year_stats,
        "expected_start_year": 2000,
        "coverage_complete": first_date and first_date.startswith("2000") if first_date else False
    }


# B3 COTAHIST endpoints disabled - Investing.com is the single data source
# @router.post("/ingest/b3/range")
# @router.post("/ingest/b3/{year}")
