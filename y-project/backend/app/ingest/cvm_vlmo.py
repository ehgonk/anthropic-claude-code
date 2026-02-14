"""
Ingestão de dados de insider trading da CVM (dataset VLMO).

A CVM disponibiliza CSVs em:
  https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/

Cada arquivo contém negociações de administradores: quem comprou/vendeu,
quanto, a que preço, em que data.
"""

import csv
import io
import logging
import zipfile
from datetime import date, datetime
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.stock import Company, InsiderTrade

logger = logging.getLogger(__name__)

CVM_VLMO_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS"


def _normalize_ticker(raw: str) -> str | None:
    """Extrai ticker limpo. Ex: 'PETR4' de variações como 'PETR4F', espaços, etc."""
    ticker = raw.strip().upper()
    if not ticker or len(ticker) < 4:
        return None
    # Remove sufixo F (fracionário) se houver
    if len(ticker) > 5 and ticker.endswith("F"):
        ticker = ticker[:-1]
    return ticker


def _parse_date(date_str: str) -> date | None:
    """Parse de data nos formatos comuns da CVM."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _safe_float(val: str) -> float:
    """Converte string para float de forma segura."""
    try:
        cleaned = val.strip().replace(",", ".")
        return float(cleaned) if cleaned else 0.0
    except (ValueError, AttributeError):
        return 0.0


async def download_vlmo_file(year: int, dest_dir: Path | None = None) -> Path:
    """Baixa o arquivo VLMO de um ano específico da CVM."""
    dest_dir = dest_dir or settings.data_dir / "raw" / "cvm"
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = f"vlmo_cia_aberta_{year}.csv"
    zip_filename = f"vlmo_cia_aberta_{year}.zip"
    dest_path = dest_dir / filename

    if dest_path.exists():
        logger.info("Arquivo %s já existe, pulando download.", filename)
        return dest_path

    # Tenta CSV direto primeiro, depois ZIP
    for url_file in [filename, zip_filename]:
        url = f"{CVM_VLMO_URL}/{url_file}"
        logger.info("Tentando download: %s", url)
        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    if url_file.endswith(".zip"):
                        z = zipfile.ZipFile(io.BytesIO(resp.content))
                        csv_names = [n for n in z.namelist() if n.endswith(".csv")]
                        if csv_names:
                            dest_path.write_bytes(z.read(csv_names[0]))
                            logger.info("Extraído %s do ZIP.", csv_names[0])
                            return dest_path
                    else:
                        dest_path.write_bytes(resp.content)
                        logger.info("Download concluído: %s", filename)
                        return dest_path
        except httpx.HTTPError as e:
            logger.warning("Falha ao baixar %s: %s", url, e)

    raise FileNotFoundError(f"Não foi possível baixar dados VLMO para {year}")


def parse_vlmo_csv(file_path: Path) -> list[dict]:
    """
    Parseia CSV da CVM VLMO e retorna lista de dicts normalizados.

    O CSV da CVM tem encoding latin-1 e separador ;
    Colunas típicas: CNPJ_Companhia, Denominacao_Social, Data_Negociacao,
    Codigo_Negociacao, Tipo_Operacao, Quantidade, Preco, Volume,
    Nome_Administrador, Cargo_Administrador, etc.
    """
    records = []

    with open(file_path, encoding="latin-1", newline="") as f:
        # Detecta separador
        sample = f.read(2048)
        f.seek(0)
        sep = ";" if ";" in sample else ","

        reader = csv.DictReader(f, delimiter=sep)

        for row in reader:
            # Mapeia colunas (CVM muda nomes entre anos)
            ticker_raw = (
                row.get("Codigo_Negociacao", "")
                or row.get("CodNeg", "")
                or row.get("codigo_negociacao", "")
                or ""
            )
            ticker = _normalize_ticker(ticker_raw)
            if not ticker:
                continue

            trade_date = _parse_date(
                row.get("Data_Negociacao", "")
                or row.get("DataNeg", "")
                or row.get("data_negociacao", "")
                or ""
            )
            if not trade_date:
                continue

            trade_type_raw = (
                row.get("Tipo_Operacao", "")
                or row.get("TipoOper", "")
                or row.get("tipo_operacao", "")
                or ""
            ).strip().upper()

            if "COMPRA" in trade_type_raw or "AQUISI" in trade_type_raw:
                trade_type = "Compra"
            elif "VENDA" in trade_type_raw or "ALIEN" in trade_type_raw:
                trade_type = "Venda"
            else:
                trade_type = trade_type_raw or "Outro"

            quantity = _safe_float(
                row.get("Quantidade", "") or row.get("Qtde", "") or row.get("quantidade", "") or "0"
            )
            price = _safe_float(
                row.get("Preco", "") or row.get("preco", "") or "0"
            )
            volume = _safe_float(
                row.get("Volume", "") or row.get("volume", "") or "0"
            )
            if volume == 0 and quantity > 0 and price > 0:
                volume = quantity * price

            records.append(
                {
                    "ticker": ticker,
                    "company_name": (
                        row.get("Denominacao_Social", "")
                        or row.get("DenomSocial", "")
                        or row.get("denominacao_social", "")
                        or ""
                    ).strip(),
                    "cnpj": (
                        row.get("CNPJ_Companhia", "")
                        or row.get("CNPJ", "")
                        or row.get("cnpj_companhia", "")
                        or ""
                    ).strip(),
                    "insider_name": (
                        row.get("Nome_Administrador", "")
                        or row.get("NomeAdm", "")
                        or row.get("nome_administrador", "")
                        or "Não informado"
                    ).strip(),
                    "insider_role": (
                        row.get("Cargo_Administrador", "")
                        or row.get("CargoAdm", "")
                        or row.get("cargo_administrador", "")
                        or ""
                    ).strip(),
                    "trade_type": trade_type,
                    "quantity": quantity,
                    "price": price,
                    "volume": volume,
                    "trade_date": trade_date,
                    "report_date": _parse_date(
                        row.get("Data_Comunicado", "")
                        or row.get("DataCom", "")
                        or row.get("data_comunicado", "")
                        or ""
                    ),
                    "intermediary": (
                        row.get("Intermediario", "")
                        or row.get("intermediario", "")
                        or ""
                    ).strip(),
                }
            )

    logger.info("Parseados %d registros de %s", len(records), file_path.name)
    return records


async def ingest_vlmo_year(db: AsyncSession, year: int) -> int:
    """Baixa e ingere dados VLMO de um ano no banco."""
    file_path = await download_vlmo_file(year)
    records = parse_vlmo_csv(file_path)

    if not records:
        logger.warning("Nenhum registro encontrado para %d", year)
        return 0

    # Upsert companies
    tickers_seen: set[str] = set()
    for rec in records:
        if rec["ticker"] not in tickers_seen and rec["company_name"]:
            tickers_seen.add(rec["ticker"])
            existing = await db.execute(
                select(Company).where(Company.ticker == rec["ticker"])
            )
            if not existing.scalar_one_or_none():
                db.add(Company(
                    ticker=rec["ticker"],
                    name=rec["company_name"],
                    cnpj=rec["cnpj"],
                ))

    # Insert trades (batch)
    batch_size = 500
    inserted = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        for rec in batch:
            db.add(InsiderTrade(
                ticker=rec["ticker"],
                company_name=rec["company_name"],
                cnpj=rec["cnpj"],
                insider_name=rec["insider_name"],
                insider_role=rec["insider_role"],
                trade_type=rec["trade_type"],
                quantity=rec["quantity"],
                price=rec["price"],
                volume=rec["volume"],
                trade_date=rec["trade_date"],
                report_date=rec["report_date"],
                intermediary=rec["intermediary"],
            ))
        await db.flush()
        inserted += len(batch)

    await db.commit()
    logger.info("Inseridos %d trades do ano %d", inserted, year)
    return inserted
