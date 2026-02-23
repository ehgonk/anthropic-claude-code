#!/usr/bin/env python3
"""
Download histórico completo desde 2000

Baixa dados históricos das ações brasileiras do Yahoo Finance
desde 2000-01-01 até hoje e salva no banco de dados.

FONTE ÚNICA: Yahoo Finance
- API oficial e gratuita
- Sem rate limiting
- Retry automático

Uso:
    python scripts/download_historical.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Stock, StockPrice
from app.services.yahoo_finance_service import yahoo_finance_service
from app.config.b3_stocks import ALL_B3_STOCKS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def download_and_save_stocks():
    """Download historical data and save to database"""

    # Date range: from 2000 to today
    start_date = datetime(2000, 1, 1)
    end_date = datetime.now()

    # Get all B3 stocks
    symbols = ALL_B3_STOCKS

    logger.info("=" * 70)
    logger.info("📥 DOWNLOAD DE DADOS HISTÓRICOS - YAHOO FINANCE")
    logger.info("=" * 70)
    logger.info(f"📅 Período: {start_date.date()} até {end_date.date()}")
    logger.info(f"📊 Ações: {len(symbols)} símbolos")
    logger.info(f"💰 Moeda: R$ (Real)")
    logger.info(f"🌐 Fonte: Yahoo Finance API")
    logger.info("")

    # Fetch data from Yahoo Finance
    logger.info("🔍 Buscando dados do Yahoo Finance...")
    logger.info("")

    stock_data = await yahoo_finance_service.fetch_stock_data(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )

    if not stock_data:
        logger.error("❌ Nenhum dado retornado do Yahoo Finance")
        return

    logger.info("")
    logger.info(f"✅ {len(stock_data)} ações baixadas com sucesso")
    logger.info("")

    # Save to database
    logger.info("💾 Salvando no banco de dados...")

    total_stocks = 0
    total_prices = 0

    async with AsyncSessionLocal() as db:
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
                    logger.info(f"  ➕ {symbol}: criada nova ação")
                else:
                    stock.name = data['name']
                    stock.price = data['price']
                    stock.change_percent = data['change_percent']
                    stock.volume = data['volume']
                    stock.updated_at = datetime.utcnow()
                    logger.info(f"  🔄 {symbol}: atualizada")

                # Count existing prices to avoid duplicates
                existing_dates = set()
                result = await db.execute(
                    select(StockPrice.date).where(StockPrice.stock_id == stock.id)
                )
                existing_dates = {row[0] for row in result.all()}

                # Add price records (skip duplicates)
                new_prices = 0
                for price in data['prices']:
                    if price['date'] in existing_dates:
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
                    new_prices += 1
                    total_prices += 1

                logger.info(f"     📈 {new_prices} preços novos (total: {len(data['prices'])})")
                total_stocks += 1

                # Commit each stock to avoid losing progress
                await db.commit()

            except Exception as e:
                logger.error(f"  ❌ Erro ao salvar {symbol}: {e}")
                await db.rollback()
                continue

    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ DOWNLOAD CONCLUÍDO")
    logger.info("=" * 70)
    logger.info(f"📊 Ações processadas: {total_stocks}")
    logger.info(f"📈 Preços inseridos: {total_prices:,}")
    logger.info(f"📅 Período: {start_date.date()} a {end_date.date()}")
    logger.info("")


if __name__ == "__main__":
    asyncio.run(download_and_save_stocks())
