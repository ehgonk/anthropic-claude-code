"""
Ibovespa Data Management API

Endpoints for managing Ibovespa historical data:
- Automatic download from Yahoo Finance (FONTE ÚNICA)
- Manual upload (CSV file as fallback)
- Data information and statistics
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import io
import csv
from datetime import datetime, timedelta
import logging
import httpx

from ..services.ibovespa_service import ibovespa_service
from ..services.yahoo_finance_service import yahoo_finance_service

router = APIRouter(prefix="/ibovespa", tags=["ibovespa"])
logger = logging.getLogger(__name__)


@router.post("/upload/csv")
async def upload_ibovespa_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload Ibovespa historical data from CSV file (fallback method)

    Expected CSV format:
    Data,Abertura,Máxima,Mínima,Fechamento,Volume
    01/07/1994,100.00,105.00,98.00,103.50,1000000

    Note: Primary data source is Yahoo Finance via /download/yahoo endpoint.
    This upload is only for manual fallback scenarios.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")

    try:
        # Read file content
        content = await file.read()
        text = content.decode('utf-8-sig')  # Handle BOM

        # Parse CSV
        reader = csv.DictReader(io.StringIO(text))
        records = []

        for row in reader:
            try:
                # B3 format: dd/mm/yyyy
                date_str = row.get('Data') or row.get('data')
                if not date_str:
                    continue

                date = datetime.strptime(date_str.strip(), "%d/%m/%Y").date()

                # Skip dates before 1994 (Real currency)
                if date.year < 1994:
                    continue

                record = {
                    'date': date,
                    'open': float(row.get('Abertura') or row.get('abertura') or row.get('Open') or 0),
                    'high': float(row.get('Máxima') or row.get('maxima') or row.get('High') or 0),
                    'low': float(row.get('Mínima') or row.get('minima') or row.get('Low') or 0),
                    'close': float(row.get('Fechamento') or row.get('fechamento') or row.get('Close') or 0),
                    'volume': int(float(row.get('Volume') or row.get('volume') or 0))
                }
                records.append(record)

            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row: {e}")
                continue

        if not records:
            raise HTTPException(status_code=400, detail="No valid records found in CSV")

        # Update database
        inserted = await ibovespa_service.update_database(records)

        return {
            "status": "success",
            "records_processed": len(records),
            "records_inserted": inserted,
            "records_skipped": len(records) - inserted,
            "first_date": str(records[0]['date']),
            "last_date": str(records[-1]['date'])
        }

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Use UTF-8 or UTF-8-BOM")
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/info")
async def get_ibovespa_info() -> Dict[str, Any]:
    """
    Get Ibovespa data information

    Returns statistics about Ibovespa data in the database
    """
    from ..database import AsyncSessionLocal
    from ..models import Stock, StockPrice
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        # Get IBOV stock
        result = await db.execute(
            select(Stock).where(Stock.symbol == 'IBOV')
        )
        stock = result.scalar_one_or_none()

        if not stock:
            return {
                "status": "not_found",
                "message": "Ibovespa data not available. Please upload CSV file.",
                "total_records": 0
            }

        # Get stats
        stats_result = await db.execute(
            select(
                func.count(StockPrice.id).label('total'),
                func.min(StockPrice.date).label('first_date'),
                func.max(StockPrice.date).label('last_date')
            ).where(StockPrice.stock_id == stock.id)
        )
        stats = stats_result.first()

        return {
            "status": "available",
            "symbol": stock.symbol,
            "name": stock.name,
            "current_price": stock.price,
            "change_percent": stock.change_percent,
            "total_records": stats.total,
            "first_date": stats.first_date,
            "last_date": stats.last_date,
            "upload_url": "/api/ibovespa/upload/csv"
        }


@router.post("/download/yahoo")
async def download_from_yahoo(
    days: int = 365,
    force_full: bool = False
) -> Dict[str, Any]:
    """
    Download Ibovespa data from Yahoo Finance (RECOMMENDED - FONTE ÚNICA)

    Este é o método principal para buscar dados históricos do Ibovespa.
    Yahoo Finance: confiável, estável, sem bloqueios.

    Args:
        days: Número de dias de histórico (padrão: 365)
        force_full: Se True, busca histórico completo desde 1994

    Returns:
        Success: Records processed and inserted
        Failure: Error message with alternatives

    Examples:
        POST /api/ibovespa/download/yahoo?days=730  # Últimos 2 anos
        POST /api/ibovespa/download/yahoo?force_full=true  # Desde 1994
    """
    logger.info(f"🔄 Downloading Ibovespa data from Yahoo Finance ({days} days)...")

    try:
        # Calculate date range
        end_date = datetime.now()
        if force_full:
            # Full history: from 1994 (Real currency start)
            start_date = datetime(1994, 7, 1)
            logger.info("📥 Downloading FULL historical data from 1994...")
        else:
            # Incremental: fetch last N days
            start_date = end_date - timedelta(days=days)
            logger.info(f"📥 Downloading last {days} days...")

        # Fetch data from Yahoo Finance
        records = await yahoo_finance_service.fetch_ibovespa_historical(
            start_date=start_date,
            end_date=end_date
        )

        if not records:
            raise HTTPException(
                status_code=404,
                detail="No data returned from Yahoo Finance"
            )

        logger.info(f"✅ Fetched {len(records)} records from Yahoo Finance")

        # Update database
        inserted = await ibovespa_service.update_database(records)

        return {
            "status": "success",
            "source": "yahoo_finance",
            "records_fetched": len(records),
            "records_inserted": inserted,
            "records_skipped": len(records) - inserted,
            "first_date": str(records[0]['date']),
            "last_date": str(records[-1]['date']),
            "date_range_days": days
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading from Yahoo Finance: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "yahoo_finance_download_failed",
                "message": f"Failed to download from Yahoo Finance: {str(e)}",
                "alternatives": [
                    {
                        "method": "manual_upload",
                        "endpoint": "POST /api/ibovespa/upload/csv",
                        "description": "Upload CSV file manually"
                    }
                ]
            }
        )


@router.get("/test/yahoo")
async def test_yahoo_connection() -> Dict[str, Any]:
    """
    Test connection to Yahoo Finance

    Returns:
        Connection status
    """
    result = await yahoo_finance_service.test_connection()
    return {
        "status": "tested",
        "source": "yahoo_finance",
        **result
    }


@router.get("/debug/yahoo")
async def debug_yahoo_finance() -> Dict[str, Any]:
    """
    Debug endpoint to test Yahoo Finance direct HTTP API with different symbols

    Tests multiple symbols to verify connectivity and data availability
    """
    symbols_to_test = [
        "^BVSP",      # Ibovespa index
        "PETR4.SA",   # Petrobras
        "VALE3.SA",   # Vale
        "ITUB4.SA",   # Itaú Unibanco
    ]

    results = []
    for symbol in symbols_to_test:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            records = await yahoo_finance_service._fetch_chart_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval="1d"
            )

            if records:
                latest = records[-1]
                results.append({
                    "symbol": symbol,
                    "success": True,
                    "records_count": len(records),
                    "first_date": str(records[0]['date']),
                    "last_date": str(latest['date']),
                    "latest_close": latest['close']
                })
            else:
                results.append({
                    "symbol": symbol,
                    "success": False,
                    "error": "No records returned"
                })

        except Exception as e:
            results.append({
                "symbol": symbol,
                "success": False,
                "error": str(e)
            })

        logger.info(f"Symbol {symbol}: {'SUCCESS' if results[-1]['success'] else 'FAILED'}")

    successful = [r for r in results if r['success']]

    return {
        "status": "debug_complete",
        "method": "direct_http_api",
        "total_tested": len(symbols_to_test),
        "successful_count": len(successful),
        "tests": results,
        "recommendation": f"Use symbol: {successful[0]['symbol']}" if successful else "No symbols returned data - check network connectivity to query1.finance.yahoo.com"
    }


@router.post("/download/auto")
async def download_auto_redirect() -> Dict[str, Any]:
    """
    DEPRECATED: This endpoint redirects to Yahoo Finance
    
    Yahoo Finance is the ONLY automated data source.
    Use /download/yahoo for automatic downloads.
    """
    raise HTTPException(
        status_code=301,
        detail="Use /api/ibovespa/download/yahoo instead"
    )



