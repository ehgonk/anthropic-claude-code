"""
Stock API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from ..database import get_db
from ..models import Stock, StockPrice
from ..schemas import (
    StockResponse,
    StockListResponse,
    PriceHistoryResponse,
    StockPriceResponse
)

router = APIRouter(prefix="/stocks", tags=["stocks"])


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
    limit: int = Query(365, ge=1, le=10000, description="Maximum number of records"),
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
