"""
Admin API endpoints

Endpoints for administrative tasks like clearing database, resetting data, etc.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from sqlalchemy import select, func, delete

from ..database import AsyncSessionLocal
from ..models import Stock, StockPrice

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.delete("/database/clear")
async def clear_database() -> Dict[str, Any]:
    """
    Clear all data from the database

    ⚠️ WARNING: This will delete ALL stocks and price data!
    Use with caution. Cannot be undone.

    Returns:
        Count of deleted records
    """
    logger.warning("⚠️ Clearing database - deleting all data...")

    async with AsyncSessionLocal() as db:
        # Count records before deletion
        stock_count = (await db.execute(select(func.count(Stock.id)))).scalar()
        price_count = (await db.execute(select(func.count(StockPrice.id)))).scalar()

        logger.info(f"📊 Current data: {stock_count} stocks, {price_count} price records")

        # Delete all price records
        await db.execute(delete(StockPrice))
        await db.commit()

        # Delete all stocks
        await db.execute(delete(Stock))
        await db.commit()

        logger.info(f"✅ Database cleared successfully")

        return {
            "status": "success",
            "message": "Database cleared successfully",
            "deleted": {
                "stocks": stock_count,
                "price_records": price_count
            }
        }


@router.post("/database/reset")
async def reset_database() -> Dict[str, Any]:
    """
    Reset database and prepare for fresh Yahoo Finance data

    This endpoint:
    1. Clears all existing data
    2. Prepares database for Yahoo Finance data

    Returns:
        Status and next steps
    """
    logger.info("🔄 Resetting database...")

    # Clear database
    clear_result = await clear_database()

    logger.info("✅ Database reset complete - ready for Yahoo Finance data")

    return {
        "status": "success",
        "message": "Database reset complete",
        "cleared": clear_result["deleted"],
        "next_steps": [
            {
                "step": 1,
                "action": "Download Ibovespa data",
                "endpoint": "POST /api/ibovespa/download/yahoo",
                "description": "Fetch Ibovespa historical data from Yahoo Finance"
            },
            {
                "step": 2,
                "action": "Trigger stock data update",
                "endpoint": "POST /api/update/run",
                "description": "Fetch stock data from Yahoo Finance"
            }
        ],
        "notes": [
            "Database has been cleared",
            "Data source: Yahoo Finance (ÚNICA FONTE)",
            "Run the endpoints above to populate database with fresh data"
        ]
    }
