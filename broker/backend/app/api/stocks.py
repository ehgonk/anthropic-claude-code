"""
Stock API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from ..database import get_db
from ..models import Stock, StockPrice
from ..schemas import (
    StockResponse,
    StockListResponse,
    PriceHistoryResponse,
    StockPriceResponse
)
from ..services.yahoo_finance_service import yahoo_finance_service

router = APIRouter(prefix="/stocks", tags=["stocks"])
logger = logging.getLogger(__name__)


@router.get("", response_model=StockListResponse)
async def list_stocks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by symbol or name"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all stocks with pagination

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **search**: Filter by symbol or company name (optional)
    """
    # Build query
    query = select(Stock)

    # Apply search filter
    if search:
        search_term = f"%{search.upper()}%"
        query = query.where(
            (Stock.symbol.ilike(search_term)) |
            (Stock.name.ilike(search_term))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Stock.symbol).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    stocks = result.scalars().all()

    return StockListResponse(
        total=total,
        page=page,
        page_size=page_size,
        stocks=[StockResponse.model_validate(stock) for stock in stocks]
    )


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific stock

    - **symbol**: Stock ticker symbol (e.g., PETR4, VALE3)
    """
    query = select(Stock).where(Stock.symbol == symbol.upper())
    result = await db.execute(query)
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    return StockResponse.model_validate(stock)


@router.get("/{symbol}/prices", response_model=PriceHistoryResponse)
async def get_stock_prices(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10000, ge=1, le=10000, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get price history for a stock

    - **symbol**: Stock ticker symbol (e.g., PETR4)
    - **start_date**: Filter prices from this date (YYYY-MM-DD)
    - **end_date**: Filter prices until this date (YYYY-MM-DD)
    - **limit**: Maximum number of records to return (default 365, max 10000)
    """
    # Get stock
    stock_query = select(Stock).where(Stock.symbol == symbol.upper())
    stock_result = await db.execute(stock_query)
    stock = stock_result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    # Build prices query
    query = select(StockPrice).where(StockPrice.stock_id == stock.id)

    # Apply date filters
    if start_date:
        query = query.where(StockPrice.date >= start_date)
    if end_date:
        query = query.where(StockPrice.date <= end_date)

    # Order by date descending (most recent first)
    query = query.order_by(StockPrice.date.desc()).limit(limit)

    # Execute query
    result = await db.execute(query)
    prices = result.scalars().all()

    return PriceHistoryResponse(
        symbol=symbol.upper(),
        start_date=start_date,
        end_date=end_date,
        total=len(prices),
        prices=[StockPriceResponse.model_validate(price) for price in prices]
    )


@router.get("/{symbol}/latest", response_model=StockPriceResponse)
async def get_latest_price(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the most recent price for a stock

    - **symbol**: Stock ticker symbol (e.g., PETR4)
    """
    # Get stock
    stock_query = select(Stock).where(Stock.symbol == symbol.upper())
    stock_result = await db.execute(stock_query)
    stock = stock_result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    # Get latest price
    query = (
        select(StockPrice)
        .where(StockPrice.stock_id == stock.id)
        .order_by(StockPrice.date.desc())
        .limit(1)
    )

    result = await db.execute(query)
    price = result.scalar_one_or_none()

    if not price:
        raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")

    return StockPriceResponse.model_validate(price)


@router.post("/download/yahoo")
async def download_stocks_from_yahoo(
    days: int = Query(365, description="Days of historical data"),
    dataset: str = Query("all", description="Dataset: 'popular' (15), 'ibovespa' (~85), or 'all' (~170)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Download Brazilian stocks from Yahoo Finance

    Downloads data for stocks and saves to database with price history.

    Args:
        days: Number of days of historical data (default: 365)
        dataset: Which dataset to download:
            - 'popular': 15 most popular stocks
            - 'ibovespa': ~85 Ibovespa index stocks
            - 'all': ~170 B3 stocks (all major liquid stocks)
    """
    logger.info(f"📥 Downloading {dataset} stocks from Yahoo Finance ({days} days)...")

    try:
        # Fetch stock data from Yahoo Finance based on dataset
        if dataset == "popular":
            stock_data = await yahoo_finance_service.get_popular_stocks(days=days)
        elif dataset == "ibovespa":
            stock_data = await yahoo_finance_service.get_ibovespa_stocks(days=days)
        elif dataset == "all":
            stock_data = await yahoo_finance_service.get_all_b3_stocks(days=days)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid dataset '{dataset}'. Use 'popular', 'ibovespa', or 'all'"
            )

        if not stock_data:
            raise HTTPException(status_code=404, detail="No stock data returned from Yahoo Finance")

        total_prices = 0
        stocks_updated = 0

        for symbol, data in stock_data.items():
            try:
                # Check if stock exists
                result = await db.execute(select(Stock).where(Stock.symbol == symbol))
                stock = result.scalar_one_or_none()

                if not stock:
                    stock = Stock(
                        symbol=symbol,
                        name=data['name'],
                        price=data['price'],
                        change_percent=data['change_percent'],
                        volume=data['volume'],
                        updated_at=datetime.utcnow()
                    )
                    db.add(stock)
                    await db.flush()
                else:
                    stock.name = data['name']
                    stock.price = data['price']
                    stock.change_percent = data['change_percent']
                    stock.volume = data['volume']
                    stock.updated_at = datetime.utcnow()

                # Add price records (skip duplicates)
                for price in data['prices']:
                    existing = await db.execute(
                        select(StockPrice).where(
                            StockPrice.stock_id == stock.id,
                            StockPrice.date == price['date']
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    db.add(StockPrice(
                        stock_id=stock.id,
                        date=price['date'],
                        open=price['open'],
                        high=price['high'],
                        low=price['low'],
                        close=price['close'],
                        volume=price['volume'],
                    ))
                    total_prices += 1

                stocks_updated += 1
                logger.info(f"✅ {symbol}: saved")

            except Exception as e:
                logger.error(f"❌ Failed to save {symbol}: {e}")
                continue

        await db.commit()

        return {
            "status": "success",
            "source": "yahoo_finance",
            "dataset": dataset,
            "stocks_downloaded": stocks_updated,
            "price_records_inserted": total_prices,
            "symbols": list(stock_data.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
