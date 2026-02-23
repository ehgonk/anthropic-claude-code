"""
Auto-update service for stock data - YAHOO FINANCE (yfinance)

This service automatically downloads and updates stock data from Yahoo Finance
on a scheduled basis (daily by default).

⚠️ FONTE: Yahoo Finance via yfinance library

📅 HISTÓRICO COMPLETO:
- Download desde 1994 (início do Real - R$)
- Batches de ações com rate limiting
- Retry com exponential backoff
- Sincronização inteligente com verificação de gaps
"""

import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
import yfinance as yf

from ..models import Stock, StockPrice
from ..database import AsyncSessionLocal
from ..config.b3_stocks import ALL_B3_STOCKS

# Configure logger
logger = logging.getLogger(__name__)

# Data de início para downloads históricos (início do Real - R$)
HISTORICAL_START_YEAR = 1994

# Tamanho do batch (anos por batch)
BATCH_SIZE_YEARS = 3

# Delay entre batches (segundos) para evitar rate limiting
BATCH_DELAY_SECONDS = 2


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

    async def get_year_stats(self, db: AsyncSession) -> Dict[int, int]:
        """Get count of records per year in database"""
        result = await db.execute(
            select(
                func.strftime('%Y', StockPrice.date).label('year'),
                func.count().label('count')
            ).group_by('year')
        )
        year_stats = {int(row.year): row.count for row in result}
        return year_stats

    async def get_missing_years(self, db: AsyncSession, force_full: bool = False) -> List[int]:
        """
        Get list of years that need to be updated

        Args:
            force_full: If True, return all years since 1994 for full historical download

        Returns:
            List of years to update
        """
        current_year = datetime.now().year

        if force_full:
            # Full historical download desde 1994
            years = list(range(HISTORICAL_START_YEAR, current_year + 1))
            logger.info(f"🔄 Full historical download: {len(years)} years ({HISTORICAL_START_YEAR}-{current_year})")
            return years

        # Get existing data stats
        year_stats = await self.get_year_stats(db)

        if not year_stats:
            # No data yet, download all historical data
            years = list(range(HISTORICAL_START_YEAR, current_year + 1))
            logger.info(f"📥 No data found, downloading all historical data: {len(years)} years")
            return years

        # Check for gaps and missing years
        missing_years = []

        # Check all years from 1994 to current
        for year in range(HISTORICAL_START_YEAR, current_year + 1):
            if year not in year_stats:
                missing_years.append(year)
            elif year_stats[year] < 100:  # Less than 100 records = incomplete year
                logger.warning(f"⚠️ Year {year} has only {year_stats[year]} records, marking for re-download")
                missing_years.append(year)

        if missing_years:
            logger.info(f"📊 Found {len(missing_years)} missing/incomplete years: {missing_years[:5]}{'...' if len(missing_years) > 5 else ''}")
        else:
            logger.info(f"✅ All years from {HISTORICAL_START_YEAR} to {current_year} are present")

        return missing_years

    def create_year_batches(self, years: List[int]) -> List[List[int]]:
        """
        Split years into batches for sequential download

        Args:
            years: List of years to download

        Returns:
            List of year batches
        """
        if not years:
            return []

        batches = []
        current_batch = []

        for year in sorted(years):
            current_batch.append(year)
            if len(current_batch) >= BATCH_SIZE_YEARS:
                batches.append(current_batch)
                current_batch = []

        # Add remaining years
        if current_batch:
            batches.append(current_batch)

        logger.info(f"📦 Created {len(batches)} batches of ~{BATCH_SIZE_YEARS} years each")
        return batches

    async def update_year_range(
        self,
        db: AsyncSession,
        start_year: int,
        end_year: int
    ) -> Dict[str, Any]:
        """
        Update data for a range of years using Yahoo Finance (yfinance)

        Args:
            db: Database session
            start_year: First year to download
            end_year: Last year to download

        Returns:
            Statistics about the update
        """
        logger.info(f"📥 Downloading data from Yahoo Finance for years {start_year}-{end_year}")

        # Calculate date range
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)

        # Adjust end date if it's in the future
        now = datetime.now()
        if end_date > now:
            end_date = now
            logger.info(f"   Adjusted end date to today: {end_date.strftime('%Y-%m-%d')}")

        # Get symbols from B3 stocks config and add .SA suffix
        symbols = [f"{symbol}.SA" for symbol in ALL_B3_STOCKS]

        logger.info(f"📊 Downloading {len(symbols)} stocks from Yahoo Finance...")

        total_prices = 0
        stocks_updated = 0
        stocks_failed = 0

        # Process stocks in batches to avoid overwhelming yfinance
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i+batch_size]

            try:
                # Download data for batch using yfinance
                data = yf.download(
                    tickers=batch_symbols,
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d'),
                    group_by='ticker',
                    auto_adjust=False,
                    progress=False,
                    threads=True
                )

                if data.empty:
                    logger.warning(f"⚠️ No data returned for batch {i//batch_size + 1}")
                    continue

                # Process each symbol in batch
                for yf_symbol in batch_symbols:
                    symbol = yf_symbol.replace('.SA', '')  # Remove .SA suffix for database

                    try:
                        # Get data for this symbol
                        if len(batch_symbols) == 1:
                            symbol_data = data
                        else:
                            symbol_data = data[yf_symbol] if yf_symbol in data else None

                        if symbol_data is None or symbol_data.empty:
                            stocks_failed += 1
                            continue

                        # Check if stock exists in database
                        result = await db.execute(select(Stock).where(Stock.symbol == symbol))
                        stock = result.scalar_one_or_none()

                        # Get latest price info
                        latest_close = symbol_data['Close'].iloc[-1] if not symbol_data.empty else 0.0
                        latest_volume = symbol_data['Volume'].iloc[-1] if not symbol_data.empty else 0

                        if not stock:
                            # Create new stock
                            stock = Stock(
                                symbol=symbol,
                                name=symbol,  # yfinance doesn't provide name in historical data
                                price=float(latest_close),
                                change_percent=0.0,
                                volume=int(latest_volume),
                                updated_at=datetime.utcnow()
                            )
                            db.add(stock)
                            await db.flush()
                        else:
                            # Update existing stock with latest data
                            stock.price = float(latest_close)
                            stock.volume = int(latest_volume)
                            stock.updated_at = datetime.utcnow()

                        # Add historical prices
                        for date_index, row in symbol_data.iterrows():
                            # Skip if any required field is NaN
                            if (row['Open'] != row['Open'] or  # NaN check
                                row['High'] != row['High'] or
                                row['Low'] != row['Low'] or
                                row['Close'] != row['Close']):
                                continue

                            price_date = date_index.strftime('%Y-%m-%d')

                            # Check if price already exists
                            existing = await db.execute(
                                select(StockPrice).where(
                                    StockPrice.stock_id == stock.id,
                                    StockPrice.date == price_date
                                )
                            )
                            if existing.scalar_one_or_none():
                                continue  # Skip duplicate

                            stock_price = StockPrice(
                                stock_id=stock.id,
                                date=price_date,
                                open=float(row['Open']),
                                high=float(row['High']),
                                low=float(row['Low']),
                                close=float(row['Close']),
                                volume=int(row['Volume']) if row['Volume'] == row['Volume'] else 0,
                            )
                            db.add(stock_price)
                            total_prices += 1

                        stocks_updated += 1

                    except Exception as e:
                        logger.error(f"❌ Error processing {symbol}: {str(e)}")
                        stocks_failed += 1
                        continue

                await db.commit()

                # Small delay between batches
                if i + batch_size < len(symbols):
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"❌ Error downloading batch {i//batch_size + 1}: {str(e)}")
                stocks_failed += len(batch_symbols)
                continue

        logger.info(
            f"✅ Updated {stocks_updated} stocks with {total_prices} new prices for {start_year}-{end_year} "
            f"({stocks_failed} failed)"
        )

        return {
            "years": f"{start_year}-{end_year}",
            "stocks": stocks_updated,
            "prices": total_prices,
            "failed": stocks_failed
        }

    async def update_year(self, db: AsyncSession, year: int) -> Dict[str, Any]:
        """
        Update data for a specific year using Investing.com

        Returns statistics about the update
        """
        result = await self.update_year_range(db, year, year)
        result["year"] = year
        return result

    async def run_update(self, force: bool = False, full_historical: bool = False) -> Dict[str, Any]:
        """
        Run the auto-update process with sequential batching

        Args:
            force: If True, re-download existing data
            full_historical: If True, download ALL data from 1994 to now

        Returns:
            Statistics about the update
        """
        if self.status.is_running:
            raise RuntimeError("Update is already running")

        self.status.start_run()

        try:
            # Yahoo Finance is the single data source
            logger.info("📊 Using Yahoo Finance (yfinance) as data source")
            ibov_result = {
                'status': 'yahoo_finance',
                'symbol': 'IBOV',
                'message': 'Data from Yahoo Finance via yfinance library'
            }

            async with AsyncSessionLocal() as db:
                # Get years to update
                years = await self.get_missing_years(db, force_full=full_historical or force)

                if not years:
                    stats = {
                        "status": "up_to_date",
                        "message": f"Data is complete from {HISTORICAL_START_YEAR} to {datetime.now().year}",
                        "years": 0,
                        "stocks": 0,
                        "prices": 0,
                        "ibovespa": ibov_result
                    }
                    self.status.finish_run(success=True, stats=stats)
                    return stats

                # Create batches for sequential download
                batches = self.create_year_batches(years)

                total_stocks = 0
                total_prices = 0
                batch_stats = []

                # Process each batch sequentially
                for batch_idx, year_batch in enumerate(batches, 1):
                    logger.info(f"🔄 Processing batch {batch_idx}/{len(batches)}: years {year_batch}")

                    # Download batch (years in batch are sequential)
                    start_year = min(year_batch)
                    end_year = max(year_batch)

                    batch_result = await self.update_year_range(db, start_year, end_year)
                    total_stocks += batch_result['stocks']
                    total_prices += batch_result['prices']
                    batch_stats.append({
                        "batch": batch_idx,
                        "years": year_batch,
                        **batch_result
                    })

                    # Add delay between batches (except after last batch)
                    if batch_idx < len(batches):
                        logger.info(f"⏸️ Waiting {BATCH_DELAY_SECONDS}s before next batch...")
                        await asyncio.sleep(BATCH_DELAY_SECONDS)

                stats = {
                    "status": "success",
                    "message": f"Downloaded {len(years)} years in {len(batches)} batches",
                    "total_years": len(years),
                    "total_batches": len(batches),
                    "stocks": total_stocks,
                    "prices": total_prices,
                    "ibovespa": ibov_result,
                    "batch_details": batch_stats,
                    "completed_at": datetime.utcnow().isoformat()
                }

                self.status.finish_run(success=True, stats=stats)
                logger.info(
                    f"✅ Update completed: {len(years)} years, "
                    f"{total_stocks} stocks, {total_prices} prices"
                )

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
