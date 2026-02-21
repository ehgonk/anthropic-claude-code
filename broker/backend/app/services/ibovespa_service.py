"""
Ibovespa Historical Data Service

Service to manage Ibovespa historical data in the database.
Source: Manual upload from B3 CSV files

Note: B3 has captcha protection preventing automatic downloads.
This service handles database operations for manually uploaded Ibovespa data.

Data is stored in the same database as individual stocks, using symbol 'IBOV'.
Criteria: Data from 1994 onwards (Real currency period).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import StockPrice, Stock

logger = logging.getLogger(__name__)


class IbovespaService:
    """Service for managing Ibovespa historical data from B3 (manual upload)"""

    SYMBOL = "IBOV"
    NAME = "Índice Bovespa"
    START_YEAR = 1994  # Start from 1994 (Real currency)

    def __init__(self):
        self.session: Optional[AsyncSession] = None

    async def _ensure_ibov_stock_exists(self, db: AsyncSession) -> Stock:
        """Ensure IBOV stock entry exists in the database"""
        result = await db.execute(
            select(Stock).where(Stock.symbol == self.SYMBOL)
        )
        stock = result.scalar_one_or_none()

        if not stock:
            logger.info(f"Creating {self.SYMBOL} stock entry...")
            stock = Stock(
                symbol=self.SYMBOL,
                name=self.NAME,
                price=0.0,
                change_percent=0.0,
                volume=0
            )
            db.add(stock)
            await db.commit()
            await db.refresh(stock)
            logger.info(f"✅ Created {self.SYMBOL} entry")

        return stock

    async def get_last_date_in_db(self) -> Optional[datetime.date]:
        """Get the most recent date for IBOV in the database"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(func.max(StockPrice.date))
                .join(Stock)
                .where(Stock.symbol == self.SYMBOL)
            )
            last_date = result.scalar()

            if isinstance(last_date, str):
                return datetime.strptime(last_date, "%Y-%m-%d").date()
            return last_date

    # download_historical_data removed - now using manual upload only
    # B3 has captcha protection preventing automatic downloads

    async def update_database(self, records: List[Dict]) -> int:
        """
        Update database with Ibovespa records

        Args:
            records: List of price records

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        async with AsyncSessionLocal() as db:
            # Ensure IBOV stock exists
            stock = await self._ensure_ibov_stock_exists(db)

            # Get existing dates to avoid duplicates
            existing_dates_result = await db.execute(
                select(StockPrice.date)
                .where(StockPrice.stock_id == stock.id)
            )
            existing_dates = {
                (datetime.strptime(d, "%Y-%m-%d").date() if isinstance(d, str) else d)
                for d in existing_dates_result.scalars().all()
            }

            # Insert only new records
            new_records = 0
            for record in records:
                if record['date'] not in existing_dates:
                    price = StockPrice(
                        stock_id=stock.id,
                        date=record['date'].strftime("%Y-%m-%d"),
                        open=record['open'],
                        high=record['high'],
                        low=record['low'],
                        close=record['close'],
                        volume=record['volume']
                    )
                    db.add(price)
                    new_records += 1

            if new_records > 0:
                await db.commit()
                logger.info(f"✅ Inserted {new_records} new records for {self.SYMBOL}")

                # Update stock latest price
                latest = records[-1]
                if len(records) >= 2:
                    prev_close = records[-2]['close']
                    change_pct = ((latest['close'] - prev_close) / prev_close) * 100
                else:
                    change_pct = 0.0

                stock.price = latest['close']
                stock.change_percent = change_pct
                stock.volume = latest['volume']
                await db.commit()

            return new_records

    async def run_incremental_update(self) -> Dict:
        """
        Manual upload only - automatic updates disabled

        Returns:
            Status message indicating manual upload required
        """
        logger.info(f"⚠️ {self.SYMBOL} automatic update disabled (manual upload only)")

        # Get last date in database to show status
        last_date = await self.get_last_date_in_db()

        result = {
            'status': 'manual_only',
            'symbol': self.SYMBOL,
            'message': 'Ibovespa requires manual upload from B3',
            'last_date': str(last_date) if last_date else None,
            'upload_endpoint': '/api/ibovespa/upload/csv'
        }

        return result

    async def run_full_update(self) -> Dict:
        """
        Manual upload only - automatic updates disabled

        Returns:
            Status message indicating manual upload required
        """
        logger.info(f"⚠️ {self.SYMBOL} automatic update disabled (manual upload only)")
        return await self.run_incremental_update()


# Global instance
ibovespa_service = IbovespaService()
