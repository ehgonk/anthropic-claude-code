"""
Ibovespa Manual Upload API

Endpoints for manually uploading Ibovespa historical data from B3.
User downloads CSV/Excel from B3 website and uploads here.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import io
import csv
from datetime import datetime
import logging

from ..services.ibovespa_service import ibovespa_service

router = APIRouter(prefix="/ibovespa", tags=["ibovespa"])
logger = logging.getLogger(__name__)


@router.post("/upload/csv")
async def upload_ibovespa_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload Ibovespa historical data from B3 CSV file

    Expected CSV format (B3 format):
    Data,Abertura,Máxima,Mínima,Fechamento,Volume
    01/07/1994,100.00,105.00,98.00,103.50,1000000

    Download from: https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm
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


@router.get("/download-instructions")
async def get_download_instructions() -> Dict[str, Any]:
    """
    Get instructions for downloading Ibovespa data from B3
    """
    return {
        "title": "Como baixar dados do Ibovespa da B3",
        "steps": [
            {
                "step": 1,
                "description": "Acesse o site da B3",
                "url": "https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm"
            },
            {
                "step": 2,
                "description": "Clique em 'Download' para baixar o arquivo histórico"
            },
            {
                "step": 3,
                "description": "Salve o arquivo CSV no seu computador"
            },
            {
                "step": 4,
                "description": "Use o endpoint POST /api/ibovespa/upload/csv para fazer upload"
            }
        ],
        "csv_format": {
            "description": "Formato esperado do CSV",
            "columns": ["Data", "Abertura", "Máxima", "Mínima", "Fechamento", "Volume"],
            "date_format": "dd/mm/yyyy",
            "example": "01/07/1994,100.00,105.00,98.00,103.50,1000000"
        },
        "notes": [
            "Apenas dados a partir de 1994 serão importados (período do Real)",
            "Registros duplicados serão automaticamente ignorados",
            "O sistema aceita arquivos com encoding UTF-8 ou UTF-8-BOM"
        ]
    }
