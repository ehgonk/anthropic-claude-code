"""
Auto-update service for B3 stock data

This service automatically downloads and updates stock data from B3
on a scheduled basis (daily by default).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Stock, StockPrice
from ..database import AsyncSessionLocal
from .b3_cotahist import b3_service
from .ibovespa_service import ibovespa_service
from ..seed import TARGET_STOCKS

# Configure logger
logger = logging.getLogger(__name__)


class UpdateStatus:
    """Track update execution status"""

    def __init__(self):
        self.last_run: Optional[datetime] = None
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.is_running: bool = False
        self.stats: Dict[str, Any] = {}

    def start_run(self):
        """Mark update as started"""
        self.is_running = True
        self.last_run = datetime.utcnow()
        self.last_error = None
        self.stats = {}

    def finish_run(self, success: bool, error: Optional[str] = None, stats: Optional[Dict] = None):
        """Mark update as finished"""
        self.is_running = False
        if success:
            self.last_success = datetime.utcnow()
            if stats:
                self.stats = stats
        else:
            self.last_error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary"""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "is_running": self.is_running,
            "stats": self.stats
        }


class AutoUpdateService:
    """Service for automatic stock data updates"""

    def __init__(self):
        self.status = UpdateStatus()

    async def get_last_date(self, db: AsyncSession) -> Optional[str]:
        """Get the most recent date in the database"""
        result = await db.execute(
            select(func.max(StockPrice.date))
        )
        last_date = result.scalar_one_or_none()
        return last_date

    async def get_missing_years(self, db: AsyncSession) -> list[int]:
        """Get list of years that need to be updated"""
        last_date_str = await self.get_last_date(db)

        if not last_date_str:
            # No data yet, start from 2024
            current_year = datetime.now().year
            return list(range(2024, current_year + 1))

        # Parse last date
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
        current_date = datetime.now()

        # Check if we need to update
        days_behind = (current_date - last_date).days

        if days_behind <= 1:
            # Data is up to date
            logger.info(f"Data is up to date (last date: {last_date_str})")
            return []

        # Get years that need updating
        years_to_update = []
        year = last_date.year
        current_year = current_date.year

        while year <= current_year:
            years_to_update.append(year)
            year += 1

        return years_to_update

    async def update_year(self, db: AsyncSession, year: int) -> Dict[str, Any]:
        """
        Update data for a specific year

        Returns statistics about the update
        """
        logger.info(f"Updating data for year {year}")

        # Download and parse COTAHIST data
        stock_data = await b3_service.get_stock_data(year, symbols=TARGET_STOCKS)

        if not stock_data:
            logger.warning(f"No data found for year {year}")
            return {"year": year, "stocks": 0, "prices": 0}

        # Convert to stock records
        stock_records = b3_service.df_to_stock_records(stock_data)

        total_prices = 0
        stocks_updated = 0

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

            # Add new prices (skip duplicates)
            for price_data in stock_data['prices']:
                # Check if price already exists
                existing = await db.execute(
                    select(StockPrice).where(
                        StockPrice.stock_id == stock.id,
                        StockPrice.date == price_data['date']
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # Skip duplicate

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

            stocks_updated += 1

        await db.commit()

        logger.info(f"Updated {stocks_updated} stocks with {total_prices} new prices for year {year}")

        return {
            "year": year,
            "stocks": stocks_updated,
            "prices": total_prices
        }

    async def run_update(self, force: bool = False) -> Dict[str, Any]:
        """
        Run the auto-update process

        Args:
            force: If True, download all years. If False, only missing data.

        Returns:
            Statistics about the update
        """
        if self.status.is_running:
            raise RuntimeError("Update is already running")

        self.status.start_run()

        try:
            # Ibovespa update DISABLED (manual upload only)
            # Use POST /api/ibovespa/upload to manually upload B3 data
            logger.info("⚠️ Ibovespa auto-update disabled (manual upload only)")
            ibov_result = {
                'status': 'manual_only',
                'symbol': 'IBOV',
                'message': 'Ibovespa requires manual upload from B3'
            }

            async with AsyncSessionLocal() as db:
                # Get years to update
                if force:
                    current_year = datetime.now().year
                    years = list(range(2024, current_year + 1))
                    logger.info(f"Force update: downloading {len(years)} years")
                else:
                    years = await self.get_missing_years(db)
                    logger.info(f"Incremental update: {len(years)} years to update")

                if not years:
                    stats = {
                        "status": "up_to_date",
                        "message": "Data is already up to date",
                        "years": 0,
                        "stocks": 0,
                        "prices": 0,
                        "ibovespa": ibov_result
                    }
                    self.status.finish_run(success=True, stats=stats)
                    return stats

                # Update each year
                total_stocks = 0
                total_prices = 0
                year_stats = []

                for year in years:
                    year_result = await self.update_year(db, year)
                    total_stocks += year_result['stocks']
                    total_prices += year_result['prices']
                    year_stats.append(year_result)

                stats = {
                    "status": "success",
                    "years": len(years),
                    "stocks": total_stocks,
                    "prices": total_prices,
                    "ibovespa": ibov_result,
                    "year_details": year_stats,
                    "completed_at": datetime.utcnow().isoformat()
                }

                self.status.finish_run(success=True, stats=stats)
                logger.info(f"Update completed: {total_stocks} stocks, {total_prices} prices, Ibovespa: {ibov_result.get('status', 'unknown')}")

                return stats

        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status.finish_run(success=False, error=error_msg)
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get current update status"""
        return self.status.to_dict()


# Singleton instance
auto_update_service = AutoUpdateService()
