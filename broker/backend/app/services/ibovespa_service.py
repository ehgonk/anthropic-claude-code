"""
Ibovespa Historical Data Service

Service to download and update Ibovespa (^BVSP) historical data.
Source: B3 data via Yahoo Finance (ticker: ^BVSP)

Note: B3 has added captcha protection to direct downloads. Yahoo Finance
provides reliable access to B3 Ibovespa data without access restrictions.

Data is stored in the same database as individual stocks, using symbol 'IBOV'.
Criteria: Data from 1994 onwards (Real currency period).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import StockPrice, Stock

logger = logging.getLogger(__name__)


class IbovespaService:
    """Service for downloading and managing Ibovespa historical data from B3"""

    SYMBOL = "IBOV"
    NAME = "Índice Bovespa"
    YAHOO_SYMBOL = "^BVSP"
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

    async def download_historical_data(
        self,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None
    ) -> List[Dict]:
        """
        Download Ibovespa historical data from B3 via Yahoo Finance

        Args:
            start_date: Start date (default: 1994-01-01)
            end_date: End date (default: today)

        Returns:
            List of price records
        """
        if not start_date:
            start_date = datetime(self.START_YEAR, 1, 1).date()
        if not end_date:
            end_date = datetime.now().date()

        logger.info(f"📊 Downloading {self.SYMBOL} data from {start_date} to {end_date}...")

        try:
            # Download data from Yahoo Finance (B3 data)
            ticker = yf.Ticker(self.YAHOO_SYMBOL)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)

            if df.empty:
                logger.warning(f"⚠️ No data returned from Yahoo Finance")
                return []

            # Convert DataFrame to list of dicts
            records = []
            for date, row in df.iterrows():
                record = {
                    'date': date.date(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                }
                records.append(record)

            logger.info(f"✅ Downloaded {len(records)} records for {self.SYMBOL}")
            return records

        except Exception as e:
            logger.error(f"❌ Error downloading {self.SYMBOL} data: {e}")
            raise

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
        Run incremental update (only download missing data)

        Returns:
            Update statistics
        """
        logger.info(f"🔄 Starting incremental update for {self.SYMBOL}...")

        # Get last date in database
        last_date = await self.get_last_date_in_db()

        if last_date:
            # Download from day after last date
            start_date = last_date + timedelta(days=1)
            logger.info(f"📅 Last date in DB: {last_date}, downloading from {start_date}")
        else:
            # No data yet, download from 1994
            start_date = datetime(self.START_YEAR, 1, 1).date()
            logger.info(f"📅 No existing data, downloading from {start_date}")

        end_date = datetime.now().date()

        # Download data
        records = await self.download_historical_data(start_date, end_date)

        # Update database
        inserted = await self.update_database(records)

        result = {
            'status': 'success' if inserted > 0 else 'up_to_date',
            'symbol': self.SYMBOL,
            'records_downloaded': len(records),
            'records_inserted': inserted,
            'start_date': str(start_date),
            'end_date': str(end_date)
        }

        logger.info(f"✅ {self.SYMBOL} update completed: {result}")
        return result

    async def run_full_update(self) -> Dict:
        """
        Run full update (download all data from 1994)

        Returns:
            Update statistics
        """
        logger.info(f"🔄 Starting FULL update for {self.SYMBOL}...")

        start_date = datetime(self.START_YEAR, 1, 1).date()
        end_date = datetime.now().date()

        # Download data
        records = await self.download_historical_data(start_date, end_date)

        # Update database
        inserted = await self.update_database(records)

        result = {
            'status': 'success',
            'symbol': self.SYMBOL,
            'records_downloaded': len(records),
            'records_inserted': inserted,
            'start_date': str(start_date),
            'end_date': str(end_date)
        }

        logger.info(f"✅ {self.SYMBOL} FULL update completed: {result}")
        return result


# Global instance
ibovespa_service = IbovespaService()
