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


@router.post("/ingest/b3/range")
async def ingest_b3_range(
    start_year: int,
    end_year: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest B3 COTAHIST data for a range of years

    Downloads and parses B3 COTAHIST files for multiple years.
    Useful for loading complete historical data.

    Args:
        start_year: First year to download (e.g., 1994)
        end_year: Last year to download (e.g., 2025)

    Returns:
        Summary of ingestion for all years
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Validate years
        current_year = datetime.now().year
        if start_year < 1994 or end_year > current_year or start_year > end_year:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid year range. Must be between 1994 and {current_year}"
            )

        total_stocks = 0
        total_prices = 0
        years_processed = []
        errors = []

        # Process each year
        for year in range(start_year, end_year + 1):
            try:
                logger.info(f"📥 Processing year {year}...")

                # Download and parse COTAHIST data
                stock_data = await b3_service.get_stock_data(year, symbols=TARGET_STOCKS)

                if not stock_data:
                    errors.append(f"Year {year}: No data found")
                    continue

                # Convert to stock records
                stock_records = b3_service.df_to_stock_records(stock_data)

                # Update database
                for symbol, stock_info in stock_records.items():
                    # Check if stock exists
                    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
                    stock = result.scalar_one_or_none()

                    if not stock:
                        # Create new stock
                        stock = Stock(
                            symbol=symbol,
                            name=stock_info['name'],
                            price=stock_info['price'],
                            change_percent=stock_info['change_percent'],
                            volume=stock_info['volume'],
                            updated_at=datetime.utcnow()
                        )
                        db.add(stock)
                        await db.flush()
                    else:
                        # Update existing stock (only if this is the latest year)
                        if year == end_year:
                            stock.name = stock_info['name']
                            stock.price = stock_info['price']
                            stock.change_percent = stock_info['change_percent']
                            stock.volume = stock_info['volume']
                            stock.updated_at = datetime.utcnow()

                    # Delete old prices for this specific year only
                    year_start = f"{year}-01-01"
                    year_end_date = f"{year}-12-31"
                    await db.execute(
                        delete(StockPrice).where(
                            StockPrice.stock_id == stock.id,
                            StockPrice.date >= year_start,
                            StockPrice.date <= year_end_date
                        )
                    )

                    # Add new prices
                    for price_data in stock_info['prices']:
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
                years_processed.append(year)
                total_stocks = len(stock_records)
                logger.info(f"✅ Year {year}: {len(stock_records)} stocks, {len([p for s in stock_records.values() for p in s['prices']])} prices")

            except Exception as e:
                logger.error(f"❌ Year {year}: {str(e)}")
                errors.append(f"Year {year}: {str(e)}")
                continue

        return {
            "status": "success" if years_processed else "failed",
            "start_year": start_year,
            "end_year": end_year,
            "years_processed": years_processed,
            "total_stocks": total_stocks,
            "total_prices": total_prices,
            "errors": errors
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        if year < 1994 or year > current_year:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid year. Must be between 1994 and {current_year}"
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

            # Delete old prices for this specific year only
            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31"
            await db.execute(
                delete(StockPrice).where(
                    StockPrice.stock_id == stock.id,
                    StockPrice.date >= year_start,
                    StockPrice.date <= year_end
                )
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
