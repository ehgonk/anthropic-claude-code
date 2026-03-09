"""
Auto-update service for stock data - YAHOO FINANCE

This service automatically downloads and updates stock data from Yahoo Finance
on a scheduled basis (daily by default).

✅ FONTE: Yahoo Finance - API oficial, grátis e confiável

📅 HISTÓRICO COMPLETO:
- Download desde 2000 (26 anos de histórico)
- Dados via httpx direto à API do Yahoo Finance
- Retry automático com backoff
- Sincronização inteligente com verificação de gaps
"""

import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Stock, StockPrice
from ..database import AsyncSessionLocal
from .yahoo_finance_service import yahoo_finance_service
from ..config.b3_stocks import ALL_STOCKS

# Configure logger
logger = logging.getLogger(__name__)

# Data de início para downloads históricos (2000 - boa disponibilidade no Yahoo Finance)
HISTORICAL_START_YEAR = 2000

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
            logger.info(f"Found {len(missing_years)} missing/incomplete years: {missing_years[:5]}{'...' if len(missing_years) > 5 else ''}")
        else:
            logger.info(f"All years from {HISTORICAL_START_YEAR} to {current_year} are present and up to date")

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

        for year in years:
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
        Update data for a range of years using Investing.com

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

        # Use all exchange stocks
        symbols = ALL_STOCKS

        # Download from Yahoo Finance
        stock_records = await yahoo_finance_service.fetch_stock_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )

        if not stock_records:
            logger.warning(f"⚠️ No data found for years {start_year}-{end_year}")
            return {"years": f"{start_year}-{end_year}", "stocks": 0, "prices": 0}

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
                # Update existing stock with latest data
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
                    symbol=stock.symbol,
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

        logger.info(f"✅ Updated {stocks_updated} stocks with {total_prices} new prices for {start_year}-{end_year}")

        return {
            "years": f"{start_year}-{end_year}",
            "stocks": stocks_updated,
            "prices": total_prices
        }

    async def update_recent_data(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Busca dados recentes do Yahoo Finance: do last_date+1 ate hoje (D0).
        Sempre chamado primeiro no run_update para garantir dados atualizados.
        D0 retorna candle parcial (preco com delay ~15min) durante o pregao,
        e candle fechado apos o encerramento do pregao.
        Para D0, faz upsert (atualiza se ja existir) para refletir o preco mais recente.
        """
        from datetime import date as date_type, timedelta as td

        last_date_str = await self.get_last_date(db)
        today = date_type.today()
        today_str = today.isoformat()

        if not last_date_str:
            logger.info("Sem dados no banco, pulando update recente")
            return {"stocks": 0, "prices": 0}

        last_dt = date_type.fromisoformat(last_date_str)

        # Sempre busca ate hoje (D0). Se last_dt >= today, apenas atualiza D0 (upsert).
        # Se last_dt < today, busca dias faltando + D0.
        fetch_from = min(last_dt + td(days=1), today)
        start_date = datetime.combine(fetch_from, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())

        logger.info(f"Buscando dados recentes: {start_date.date()} ate {end_date.date()} (inclui D0 parcial)")

        stock_records = await yahoo_finance_service.fetch_stock_data(
            symbols=ALL_STOCKS,
            start_date=start_date,
            end_date=end_date
        )

        if not stock_records:
            logger.info("Nenhum dado recente encontrado no Yahoo Finance")
            return {"stocks": 0, "prices": 0}

        total_prices = 0
        stocks_updated = 0

        for symbol, stock_data in stock_records.items():
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
            if not stock:
                continue

            if stock_data.get('price'):
                stock.price = stock_data['price']
                stock.change_percent = stock_data.get('change_percent', 0)
                stock.volume = stock_data.get('volume', 0)
                stock.updated_at = datetime.utcnow()
                # Atualiza nome se Yahoo Finance retornou um nome real (nao apenas o symbol)
                if stock_data.get('name') and stock_data['name'] != symbol:
                    stock.name = stock_data['name']

            for price_data in stock_data['prices']:
                existing_row = (await db.execute(
                    select(StockPrice).where(
                        StockPrice.stock_id == stock.id,
                        StockPrice.date == price_data['date']
                    )
                )).scalar_one_or_none()

                if existing_row:
                    # D0: sempre atualizar com dados mais recentes (preco com delay ~15min)
                    if price_data['date'] == today_str:
                        existing_row.open = price_data['open']
                        existing_row.high = price_data['high']
                        existing_row.low = price_data['low']
                        existing_row.close = price_data['close']
                        existing_row.volume = price_data['volume']
                        total_prices += 1
                    # Dias anteriores: dados finais, nao sobrescrever
                    continue

                db.add(StockPrice(
                    stock_id=stock.id,
                    symbol=stock.symbol,
                    date=price_data['date'],
                    open=price_data['open'],
                    high=price_data['high'],
                    low=price_data['low'],
                    close=price_data['close'],
                    volume=price_data['volume'],
                ))
                total_prices += 1

            stocks_updated += 1

        await db.commit()
        logger.info(f"Update recente: {stocks_updated} acoes, {total_prices} precos novos/atualizados (ate D0: {today_str})")
        return {"stocks": stocks_updated, "prices": total_prices}

    async def update_year(self, db: AsyncSession, year: int) -> Dict[str, Any]:
        """Update data for a specific year"""
        result = await self.update_year_range(db, year, year)
        result["year"] = year
        return result

    async def run_update(self, force: bool = False, full_historical: bool = False) -> Dict[str, Any]:
        """
        Run the auto-update process.

        Sempre executa em duas fases:
        1. update_recent_data: busca do last_date+1 ate ontem no Yahoo Finance
           (garante que last_date == hoje-1 apos o update)
        2. get_missing_years: preenche anos historicos faltando desde HISTORICAL_START_YEAR

        Args:
            force: If True, re-download existing data
            full_historical: If True, download ALL data from HISTORICAL_START_YEAR to now
        """
        if self.status.is_running:
            raise RuntimeError("Update is already running")

        self.status.start_run()

        try:
            # Yahoo Finance is the data source
            logger.info("📊 Using Yahoo Finance as data source")
            ibov_result = {
                'status': 'yahoo_finance',
                'symbol': 'IBOV',
                'message': 'Data from Yahoo Finance API (official, free, reliable)'
            }

            async with AsyncSessionLocal() as db:
                # FASE 1: sempre atualizar dados recentes (last_date+1 ate ontem)
                recent_result = await self.update_recent_data(db)

                # FASE 2: verificar e preencher anos historicos faltando
                years = await self.get_missing_years(db, force_full=full_historical or force)

                if not years:
                    stats = {
                        "status": "up_to_date",
                        "message": f"Data is complete from {HISTORICAL_START_YEAR} to {datetime.now().year}",
                        "years": 0,
                        "stocks": recent_result["stocks"],
                        "prices": recent_result["prices"],
                        "ibovespa": ibov_result
                    }
                    self.status.finish_run(success=True, stats=stats)
                    return stats

                # Prioritize current/recent years as individual batches first
                current_year = datetime.now().year
                recent_years = sorted([y for y in years if y >= current_year - 1], reverse=True)
                old_years = sorted([y for y in years if y < current_year - 1])

                recent_batches = [[y] for y in recent_years]
                old_batches = self.create_year_batches(old_years)
                batches = recent_batches + old_batches

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
