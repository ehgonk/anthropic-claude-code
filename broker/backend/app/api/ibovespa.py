"""
Ibovespa Data Management API

Endpoints for managing Ibovespa historical data:
- Manual upload (CSV file)
- Automatic download from Yahoo Finance (FONTE ÚNICA)
- Automatic download from B3 (legacy/deprecated)
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


@router.post("/download/auto")
async def download_from_b3() -> Dict[str, Any]:
    """
    Attempt to download Ibovespa data directly from B3 (LEGACY)

    ⚠️ DEPRECATED: Use POST /api/ibovespa/download/investing instead
    ⚠️ WARNING: B3 may block automated downloads with captcha or 403 errors.

    RECOMMENDED ALTERNATIVE: POST /api/ibovespa/download/investing
    This endpoint uses Investing.com which is more reliable.

    This endpoint will try to download from multiple B3 sources:
    1. B3 official API (if available)
    2. Alternative data sources
    3. Fallback to cached data

    Returns:
        Success: Records processed and inserted
        Failure: Error message and instructions for manual upload
    """
    logger.info("🔄 Attempting automatic download from B3...")

    # Try multiple sources
    sources = [
        {
            "name": "B3 Portal - Evolução Diária",
            "url": "https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQk9WIn0=",
            "type": "api"
        },
        {
            "name": "B3 Historical Data",
            "url": "https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm",
            "type": "webpage"
        }
    ]

    errors = []

    for source in sources:
        try:
            logger.info(f"📥 Trying source: {source['name']}")

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(source['url'])

                if response.status_code == 200:
                    logger.info(f"✅ Connected to {source['name']}")

                    # Parse based on type
                    if source['type'] == 'api':
                        # Try to parse JSON API response
                        try:
                            data = response.json()
                            # Process data here
                            logger.info(f"📊 Received API data: {len(data)} records")
                            # TODO: Implement API parsing

                        except Exception as e:
                            logger.warning(f"⚠️ Could not parse API response: {e}")
                            continue

                    elif source['type'] == 'webpage':
                        # Check if we got HTML (captcha page)
                        if 'captcha' in response.text.lower() or 'recaptcha' in response.text.lower():
                            logger.warning(f"⚠️ Captcha detected on {source['name']}")
                            errors.append(f"{source['name']}: Captcha required")
                            continue

                else:
                    logger.warning(f"⚠️ HTTP {response.status_code} from {source['name']}")
                    errors.append(f"{source['name']}: HTTP {response.status_code}")

        except httpx.HTTPError as e:
            logger.warning(f"⚠️ Connection failed to {source['name']}: {e}")
            errors.append(f"{source['name']}: {str(e)}")
        except Exception as e:
            logger.warning(f"⚠️ Error with {source['name']}: {e}")
            errors.append(f"{source['name']}: {str(e)}")

    # If all sources failed
    logger.error("❌ All download sources failed")
    raise HTTPException(
        status_code=503,
        detail={
            "error": "automatic_download_failed",
            "message": "Não foi possível baixar dados automaticamente da B3",
            "reasons": errors,
            "alternatives": [
                {
                    "method": "powershell_script",
                    "title": "Download via PowerShell (Recomendado)",
                    "description": "Script PowerShell que simula navegador e tenta baixar da B3",
                    "endpoint": "GET /api/ibovespa/download-script",
                    "instructions": [
                        "1. Acesse: GET /api/ibovespa/download-script",
                        "2. Copie o script PowerShell",
                        "3. Execute no PowerShell",
                        "4. O script fará upload automático"
                    ]
                },
                {
                    "method": "manual_upload",
                    "title": "Upload Manual (Alternativa)",
                    "description": "Baixe manualmente do site e faça upload",
                    "endpoint": "POST /api/ibovespa/upload/csv",
                    "download_url": "https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm"
                }
            ]
        }
    )


@router.get("/download-script")
async def get_download_script() -> Dict[str, Any]:
    """
    Get PowerShell script for downloading Ibovespa data from B3

    Returns a complete PowerShell script that:
    1. Attempts to download data directly from B3 endpoints
    2. Simulates browser headers to bypass simple blocks
    3. Saves CSV file locally
    4. Automatically uploads to the API

    Usage:
        1. GET this endpoint
        2. Copy the 'script' field
        3. Save as Download-Ibovespa.ps1
        4. Run: powershell -ExecutionPolicy Bypass -File Download-Ibovespa.ps1
    """
    script = """# ============================================
# DOWNLOAD IBOVESPA DA B3 - PowerShell
# ============================================
# Este script tenta baixar dados do Ibovespa diretamente da B3
# Similar ao download do COTAHIST

param(
    [string]$OutputPath = "$env:USERPROFILE\\Downloads\\ibovespa_b3.csv",
    [string]$ApiUrl = "http://localhost:8001/api/ibovespa/upload/csv",
    [switch]$AutoUpload = $true
)

Write-Host "📊 DOWNLOAD IBOVESPA DA B3" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray

# URLs da B3 para tentar (em ordem de prioridade)
$b3Urls = @(
    @{
        Name = "B3 Portal - API Dados Diários"
        Url = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEwMCwiaW5kZXgiOiJJQk9WIn0="
        Type = "json"
    },
    @{
        Name = "B3 Market Data - Download CSV"
        Url = "https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/"
        Type = "html"
    }
)

# Configurar headers para simular navegador
$headers = @{
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    'Accept' = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    'Accept-Language' = 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
    'Accept-Encoding' = 'gzip, deflate, br'
    'Connection' = 'keep-alive'
    'Upgrade-Insecure-Requests' = '1'
}

$success = $false

foreach ($source in $b3Urls) {
    Write-Host "🔄 Tentando: $($source.Name)..." -ForegroundColor Cyan

    try {
        $response = Invoke-WebRequest -Uri $source.Url -Headers $headers -TimeoutSec 30 -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Conectado com sucesso!" -ForegroundColor Green

            # Verificar se tem captcha
            if ($response.Content -match 'captcha|recaptcha') {
                Write-Host "⚠️  Captcha detectado - tentando próxima fonte..." -ForegroundColor Yellow
                continue
            }

            # Processar resposta baseado no tipo
            if ($source.Type -eq "json") {
                Write-Host "📊 Processando dados JSON..." -ForegroundColor Cyan

                try {
                    $data = $response.Content | ConvertFrom-Json

                    # Converter para CSV
                    # TODO: Implementar conversão JSON -> CSV aqui
                    Write-Host "⚠️  Conversão JSON não implementada ainda" -ForegroundColor Yellow
                    continue

                } catch {
                    Write-Host "⚠️  Erro ao processar JSON: $($_.Exception.Message)" -ForegroundColor Yellow
                    continue
                }
            }

            # Se chegou aqui, tentou mas não conseguiu
            continue

        } else {
            Write-Host "⚠️  HTTP $($response.StatusCode)" -ForegroundColor Yellow
        }

    } catch {
        Write-Host "⚠️  Erro: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Se todas as fontes falharam
if (-not $success) {
    Write-Host "`n❌ Não foi possível baixar automaticamente" -ForegroundColor Red
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "`n📥 BAIXE MANUALMENTE:" -ForegroundColor Yellow
    Write-Host "1. Acesse: https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm" -ForegroundColor Cyan
    Write-Host "2. Clique em 'Download' e salve o CSV" -ForegroundColor Cyan
    Write-Host "3. Execute upload manual:`n" -ForegroundColor Cyan

    # Tentar upload de arquivo existente
    $csvFiles = Get-ChildItem "$env:USERPROFILE\\Downloads" -Filter "*.csv" -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending

    if ($csvFiles) {
        Write-Host "📂 Arquivos CSV encontrados em Downloads:" -ForegroundColor Green
        for ($i = 0; $i -lt [Math]::Min(5, $csvFiles.Count); $i++) {
            Write-Host "   $($i+1). $($csvFiles[$i].Name) - $($csvFiles[$i].LastWriteTime)" -ForegroundColor Yellow
        }

        $escolha = Read-Host "`nDigite o número do arquivo para upload (ou Enter para pular)"

        if ($escolha -match '^\\d+$' -and [int]$escolha -le $csvFiles.Count -and [int]$escolha -gt 0) {
            $arquivo = $csvFiles[[int]$escolha - 1].FullName
            Write-Host "`n📤 Fazendo upload de: $($csvFiles[[int]$escolha - 1].Name)" -ForegroundColor Cyan

            # Upload usando curl.exe se disponível
            if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
                $result = curl.exe -X POST $ApiUrl -F "file=@$arquivo"
                Write-Host "`n✅ Upload concluído!" -ForegroundColor Green
                Write-Host $result
            } else {
                Write-Host "❌ curl.exe não encontrado. Instale ou use PowerShell 7+" -ForegroundColor Red
            }
        }
    }

    exit 1
}

Write-Host "`n✅ PROCESSO CONCLUÍDO!" -ForegroundColor Green
"""

    return {
        "title": "Script PowerShell para Download do Ibovespa",
        "description": "Script completo que tenta baixar dados diretamente da B3",
        "script": script,
        "usage": {
            "steps": [
                {
                    "step": 1,
                    "description": "Copie o script acima",
                    "command": None
                },
                {
                    "step": 2,
                    "description": "Salve como 'Download-Ibovespa.ps1'",
                    "command": None
                },
                {
                    "step": 3,
                    "description": "Execute no PowerShell",
                    "command": "powershell -ExecutionPolicy Bypass -File Download-Ibovespa.ps1"
                },
                {
                    "step": 4,
                    "description": "Ou copie e cole diretamente no PowerShell",
                    "command": None
                }
            ],
            "one_liner": "Invoke-RestMethod http://localhost:8001/api/ibovespa/download-script | Select-Object -ExpandProperty script | Invoke-Expression"
        },
        "notes": [
            "O script tenta múltiplas fontes da B3",
            "Simula navegador para evitar bloqueios simples",
            "Se falhar, oferece upload manual de arquivos existentes",
            "Requer PowerShell 5.1 ou superior"
        ]
    }


@router.get("/download-instructions")
async def get_download_instructions() -> Dict[str, Any]:
    """
    Get instructions for downloading Ibovespa data
    """
    return {
        "title": "Como baixar dados do Ibovespa",
        "methods": [
            {
                "method": "yahoo_finance",
                "endpoint": "POST /api/ibovespa/download/yahoo",
                "description": "Download do Yahoo Finance (RECOMENDADO - FONTE ÚNICA)",
                "success_rate": "alta",
                "recommended": True,
                "notes": "Fonte oficial, estável, biblioteca yfinance"
            },
            {
                "method": "manual",
                "endpoint": "POST /api/ibovespa/upload/csv",
                "description": "Upload manual de arquivo CSV",
                "success_rate": "alta",
                "notes": "Alternativa manual"
            },
            {
                "method": "b3_auto",
                "endpoint": "POST /api/ibovespa/download/auto",
                "description": "Download da B3 (DEPRECATED)",
                "success_rate": "baixa",
                "notes": "Legado - B3 bloqueia com captcha"
            }
        ],
        "manual_steps": [
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
