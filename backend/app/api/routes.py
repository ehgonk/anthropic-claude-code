"""Endpoints da API REST."""

from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.stock import (
    Company,
    InsiderScore,
    InsiderTrade,
    StockPrice,
)
from app.services.scoring import calculate_all_scores, calculate_score

router = APIRouter(prefix="/api", tags=["api"])


# === Schemas ===

class CompanyOut(BaseModel):
    id: int
    ticker: str
    name: str
    cnpj: str | None = None
    sector: str | None = None

    model_config = {"from_attributes": True}


class StockPriceOut(BaseModel):
    trade_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    num_trades: int

    model_config = {"from_attributes": True}


class InsiderTradeOut(BaseModel):
    id: int
    ticker: str
    company_name: str
    insider_name: str
    insider_role: str | None = None
    trade_type: str
    quantity: float
    price: float
    volume: float
    trade_date: date
    report_date: date | None = None

    model_config = {"from_attributes": True}


class ScoreOut(BaseModel):
    ticker: str
    calc_date: date
    insider_score: float
    short_score: float
    flow_score: float
    momentum_score: float
    total_score: float
    signal: str
    insider_buy_count_30d: int
    insider_sell_count_30d: int
    insider_net_volume_30d: float

    model_config = {"from_attributes": True}


class RankingItem(BaseModel):
    ticker: str
    company_name: str
    total_score: float
    signal: str
    insider_buy_count_30d: int
    insider_sell_count_30d: int
    insider_net_volume_30d: float


class DashboardSummary(BaseModel):
    total_companies: int
    total_insider_trades: int
    recent_buys_30d: int
    recent_sells_30d: int
    top_signal: str
    last_update: date | None


class PriceWithInsiders(BaseModel):
    prices: list[StockPriceOut]
    insider_trades: list[InsiderTradeOut]
    score: ScoreOut | None = None


# === Endpoints ===

@router.get("/health")
async def health():
    return {"status": "ok", "service": "Y"}


@router.get("/companies", response_model=list[CompanyOut])
async def list_companies(
    search: str | None = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Lista empresas cadastradas. Busca por ticker ou nome."""
    query = select(Company)
    if search:
        pattern = f"%{search.upper()}%"
        query = query.where(
            (Company.ticker.ilike(pattern)) | (Company.name.ilike(pattern))
        )
    query = query.order_by(Company.ticker).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/companies/{ticker}", response_model=CompanyOut)
async def get_company(ticker: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Company).where(Company.ticker == ticker.upper())
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(404, f"Empresa {ticker} não encontrada")
    return company


@router.get("/prices/{ticker}", response_model=list[StockPriceOut])
async def get_prices(
    ticker: str,
    days: int = Query(default=365, le=1825),
    db: AsyncSession = Depends(get_db),
):
    """Retorna cotações de um ativo nos últimos N dias."""
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(StockPrice)
        .where(StockPrice.ticker == ticker.upper(), StockPrice.trade_date >= since)
        .order_by(StockPrice.trade_date.asc())
    )
    return result.scalars().all()


@router.get("/insider-trades", response_model=list[InsiderTradeOut])
async def list_insider_trades(
    ticker: str | None = None,
    days: int = Query(default=90, le=730),
    trade_type: Literal["Compra", "Venda"] | None = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Lista trades de insiders, filtrável por ticker e tipo."""
    since = date.today() - timedelta(days=days)
    query = select(InsiderTrade).where(InsiderTrade.trade_date >= since)

    if ticker:
        query = query.where(InsiderTrade.ticker == ticker.upper())
    if trade_type:
        query = query.where(InsiderTrade.trade_type == trade_type)

    query = query.order_by(InsiderTrade.trade_date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/scores/ranking", response_model=list[RankingItem])
async def get_ranking(
    limit: int = Query(default=20, le=100),
    order: Literal["asc", "desc"] = "desc",
    db: AsyncSession = Depends(get_db),
):
    """
    Ranking de empresas por score.
    desc = maiores scores primeiro (sinais de compra)
    asc = menores scores primeiro (sinais de venda)
    """
    # Pega o score mais recente de cada ticker
    subq = (
        select(
            InsiderScore.ticker,
            func.max(InsiderScore.calc_date).label("max_date"),
        )
        .group_by(InsiderScore.ticker)
        .subquery()
    )

    query = (
        select(InsiderScore)
        .join(
            subq,
            (InsiderScore.ticker == subq.c.ticker)
            & (InsiderScore.calc_date == subq.c.max_date),
        )
    )

    if order == "desc":
        query = query.order_by(InsiderScore.total_score.desc())
    else:
        query = query.order_by(InsiderScore.total_score.asc())

    query = query.limit(limit)
    result = await db.execute(query)
    scores = result.scalars().all()

    # Enriquece com nome da empresa
    items = []
    for s in scores:
        company = await db.execute(
            select(Company).where(Company.ticker == s.ticker)
        )
        company = company.scalar_one_or_none()
        items.append(
            RankingItem(
                ticker=s.ticker,
                company_name=company.name if company else s.ticker,
                total_score=s.total_score,
                signal=s.signal,
                insider_buy_count_30d=s.insider_buy_count_30d,
                insider_sell_count_30d=s.insider_sell_count_30d,
                insider_net_volume_30d=s.insider_net_volume_30d,
            )
        )

    return items


@router.get("/scores/{ticker}", response_model=ScoreOut)
async def get_score(ticker: str, db: AsyncSession = Depends(get_db)):
    """Retorna score mais recente de um ativo."""
    result = await db.execute(
        select(InsiderScore)
        .where(InsiderScore.ticker == ticker.upper())
        .order_by(InsiderScore.calc_date.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(404, f"Score não encontrado para {ticker}")
    return score


@router.get("/scores/{ticker}/history", response_model=list[ScoreOut])
async def get_score_history(
    ticker: str,
    days: int = Query(default=90, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Histórico de scores de um ativo."""
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(InsiderScore)
        .where(
            InsiderScore.ticker == ticker.upper(),
            InsiderScore.calc_date >= since,
        )
        .order_by(InsiderScore.calc_date.asc())
    )
    return result.scalars().all()


@router.get("/dashboard/{ticker}", response_model=PriceWithInsiders)
async def get_dashboard_data(
    ticker: str,
    days: int = Query(default=180, le=730),
    db: AsyncSession = Depends(get_db),
):
    """Dados consolidados para o dashboard de um ativo: preços + insiders + score."""
    ticker = ticker.upper()
    since = date.today() - timedelta(days=days)

    prices_q = await db.execute(
        select(StockPrice)
        .where(StockPrice.ticker == ticker, StockPrice.trade_date >= since)
        .order_by(StockPrice.trade_date.asc())
    )

    trades_q = await db.execute(
        select(InsiderTrade)
        .where(InsiderTrade.ticker == ticker, InsiderTrade.trade_date >= since)
        .order_by(InsiderTrade.trade_date.asc())
    )

    score_q = await db.execute(
        select(InsiderScore)
        .where(InsiderScore.ticker == ticker)
        .order_by(InsiderScore.calc_date.desc())
        .limit(1)
    )

    return PriceWithInsiders(
        prices=prices_q.scalars().all(),
        insider_trades=trades_q.scalars().all(),
        score=score_q.scalar_one_or_none(),
    )


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Resumo geral para o dashboard principal."""
    total_companies = await db.execute(select(func.count(Company.id)))
    total_trades = await db.execute(select(func.count(InsiderTrade.id)))

    d30 = date.today() - timedelta(days=30)
    recent_buys = await db.execute(
        select(func.count(InsiderTrade.id)).where(
            InsiderTrade.trade_type == "Compra",
            InsiderTrade.trade_date >= d30,
        )
    )
    recent_sells = await db.execute(
        select(func.count(InsiderTrade.id)).where(
            InsiderTrade.trade_type == "Venda",
            InsiderTrade.trade_date >= d30,
        )
    )

    last_score = await db.execute(
        select(InsiderScore).order_by(InsiderScore.calc_date.desc()).limit(1)
    )
    last = last_score.scalar_one_or_none()

    buys_count = recent_buys.scalar() or 0
    sells_count = recent_sells.scalar() or 0

    return DashboardSummary(
        total_companies=total_companies.scalar() or 0,
        total_insider_trades=total_trades.scalar() or 0,
        recent_buys_30d=buys_count,
        recent_sells_30d=sells_count,
        top_signal="COMPRA" if buys_count > sells_count else "VENDA",
        last_update=last.calc_date if last else None,
    )


@router.post("/ingest/cvm/{year}")
async def trigger_cvm_ingest(year: int, db: AsyncSession = Depends(get_db)):
    """Dispara ingestão de dados CVM VLMO para um ano."""
    from app.ingest.cvm_vlmo import ingest_vlmo_year

    try:
        count = await ingest_vlmo_year(db, year)
        return {"status": "ok", "records_inserted": count, "year": year}
    except Exception as e:
        raise HTTPException(500, f"Erro na ingestão: {e}")


@router.post("/ingest/b3/{year}")
async def trigger_b3_ingest(year: int, db: AsyncSession = Depends(get_db)):
    """Dispara ingestão de dados B3 COTAHIST para um ano."""
    from app.ingest.b3_cotahist import ingest_cotahist_year

    try:
        count = await ingest_cotahist_year(db, year)
        return {"status": "ok", "records_inserted": count, "year": year}
    except Exception as e:
        raise HTTPException(500, f"Erro na ingestão: {e}")


@router.post("/scores/recalculate")
async def trigger_recalculate(db: AsyncSession = Depends(get_db)):
    """Recalcula todos os scores."""
    count = await calculate_all_scores(db)
    return {"status": "ok", "scores_calculated": count}


@router.post("/sync/d-1")
async def sync_d1(db: AsyncSession = Depends(get_db)):
    """
    Sincronização automática D-1: baixa dados CVM e B3 do ano corrente
    e recalcula todos os scores.
    """
    import logging
    from datetime import date as dt_date

    from app.ingest.b3_cotahist import ingest_cotahist_year
    from app.ingest.cvm_vlmo import ingest_vlmo_year

    logger = logging.getLogger(__name__)
    year = dt_date.today().year
    cvm_count = 0
    b3_count = 0
    scores_count = 0

    try:
        logger.info("Sync D-1: ingestão CVM %d", year)
        cvm_count = await ingest_vlmo_year(db, year)
    except Exception as e:
        logger.warning("Sync D-1: erro CVM: %s", e)

    try:
        logger.info("Sync D-1: ingestão B3 %d", year)
        b3_count = await ingest_cotahist_year(db, year)
    except Exception as e:
        logger.warning("Sync D-1: erro B3: %s", e)

    try:
        logger.info("Sync D-1: recalculando scores")
        scores_count = await calculate_all_scores(db)
    except Exception as e:
        logger.warning("Sync D-1: erro scores: %s", e)

    return {
        "status": "ok",
        "message": f"Sync D-1 concluído para {year}",
        "cvm_records": cvm_count,
        "b3_records": b3_count,
        "scores_calculated": scores_count,
    }
