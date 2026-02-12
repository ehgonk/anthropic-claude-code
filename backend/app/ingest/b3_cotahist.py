"""
Ingestão de dados de cotações da B3 (COTAHIST).

O COTAHIST é um arquivo posicional (largura fixa) com layout documentado pela B3.
Cada linha tem 245 caracteres com campos em posições específicas.

Layout principal (registro tipo 01 — cotações diárias):
  Pos 01-02: Tipo de registro (01 = cotação)
  Pos 03-10: Data do pregão (AAAAMMDD)
  Pos 11-12: Código BDI
  Pos 13-24: Código de negociação (ticker)
  Pos 25-27: Tipo de mercado (010 = à vista)
  Pos 28-39: Nome resumido
  Pos 40-49: Especificação do papel
  Pos 57-69: Preço abertura (11 inteiros, 2 decimais)
  Pos 70-82: Preço máximo
  Pos 83-95: Preço mínimo
  Pos 96-108: Preço médio
  Pos 109-121: Preço último negócio
  Pos 148-152: Código ISIN (parcial)
  Pos 153-170: Volume total
  Pos 171-188: Quantidade de títulos negociados
"""

import logging
import zipfile
import io
from datetime import date, datetime
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.stock import StockPrice

logger = logging.getLogger(__name__)


def _extract_decimal(raw: str, decimals: int = 2) -> float:
    """Converte campo numérico posicional para float."""
    try:
        val = int(raw.strip())
        return val / (10**decimals)
    except (ValueError, TypeError):
        return 0.0


def parse_cotahist_line(line: str) -> dict | None:
    """
    Parseia uma linha do COTAHIST (layout posicional).
    Retorna dict com dados da cotação ou None se não for registro válido.
    """
    if len(line) < 200:
        return None

    tipo_reg = line[0:2]
    if tipo_reg != "01":
        return None

    # Tipo de mercado: 010 = à vista (o que nos interessa)
    market_type = int(line[24:27].strip() or "0")

    ticker = line[12:24].strip()
    if not ticker or len(ticker) < 4:
        return None

    # Filtra: só mercado à vista (010) e exercício opções (012)
    if market_type not in (10, 12):
        return None

    try:
        trade_date = datetime.strptime(line[2:10], "%Y%m%d").date()
    except ValueError:
        return None

    return {
        "ticker": ticker,
        "trade_date": trade_date,
        "open_price": _extract_decimal(line[56:69]),
        "high_price": _extract_decimal(line[69:82]),
        "low_price": _extract_decimal(line[82:95]),
        "close_price": _extract_decimal(line[108:121]),
        "volume": _extract_decimal(line[152:170]),
        "num_trades": int(line[147:152].strip() or "0"),
        "market_type": market_type,
    }


async def download_cotahist(year: int, dest_dir: Path | None = None) -> Path:
    """Baixa arquivo COTAHIST anual da B3."""
    dest_dir = dest_dir or settings.data_dir / "raw" / "b3"
    dest_dir.mkdir(parents=True, exist_ok=True)

    txt_file = dest_dir / f"COTAHIST_A{year}.TXT"
    if txt_file.exists():
        logger.info("Arquivo %s já existe, pulando download.", txt_file.name)
        return txt_file

    zip_url = f"{settings.b3_cotahist_url}/COTAHIST_A{year}.ZIP"
    logger.info("Baixando COTAHIST: %s", zip_url)

    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        resp = await client.get(zip_url)
        resp.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(resp.content))
    txt_names = [n for n in z.namelist() if n.upper().endswith(".TXT")]
    if not txt_names:
        raise FileNotFoundError(f"Nenhum TXT encontrado no ZIP COTAHIST {year}")

    txt_file.write_bytes(z.read(txt_names[0]))
    logger.info("Extraído %s (%d bytes)", txt_names[0], txt_file.stat().st_size)
    return txt_file


def parse_cotahist_file(file_path: Path) -> list[dict]:
    """Parseia arquivo COTAHIST inteiro e retorna lista de cotações."""
    records = []

    with open(file_path, encoding="latin-1") as f:
        for line in f:
            rec = parse_cotahist_line(line)
            if rec:
                records.append(rec)

    logger.info("Parseados %d registros de %s", len(records), file_path.name)
    return records


async def ingest_cotahist_year(db: AsyncSession, year: int) -> int:
    """Baixa e ingere COTAHIST de um ano no banco."""
    file_path = await download_cotahist(year)
    records = parse_cotahist_file(file_path)

    if not records:
        logger.warning("Nenhum registro COTAHIST para %d", year)
        return 0

    batch_size = 1000
    inserted = 0

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        for rec in batch:
            # Verifica se já existe
            existing = await db.execute(
                select(StockPrice).where(
                    StockPrice.ticker == rec["ticker"],
                    StockPrice.trade_date == rec["trade_date"],
                )
            )
            if existing.scalar_one_or_none():
                continue

            db.add(StockPrice(**rec))
            inserted += 1

        await db.flush()

    await db.commit()
    logger.info("Inseridos %d cotações do ano %d", inserted, year)
    return inserted
