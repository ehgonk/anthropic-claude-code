"""
Engine de scoring — calcula score de -100 a +100 por ativo.

Componentes do score:
  1. Insider Score (peso 40%): baseado em compras vs vendas de insiders nos últimos 30/60/90 dias
  2. Short Score (peso 20%): baseado em variação do short interest
  3. Flow Score (peso 20%): baseado em fluxo líquido estrangeiro
  4. Momentum Score (peso 20%): baseado em momentum técnico (tendência de preço)

Cada componente varia de -100 a +100, e o total é a média ponderada.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import (
    Company,
    InsiderScore,
    InsiderTrade,
    InvestorFlow,
    ShortInterest,
    StockPrice,
)

logger = logging.getLogger(__name__)

# Pesos dos componentes
WEIGHT_INSIDER = 0.40
WEIGHT_SHORT = 0.20
WEIGHT_FLOW = 0.20
WEIGHT_MOMENTUM = 0.20


def _clamp(value: float, min_val: float = -100.0, max_val: float = 100.0) -> float:
    return max(min_val, min(max_val, value))


async def calc_insider_component(
    db: AsyncSession, ticker: str, ref_date: date
) -> tuple[float, int, int, float]:
    """
    Calcula componente insider.

    Lógica:
    - Conta compras e vendas nos últimos 30 dias
    - Volume líquido (compras - vendas)
    - Anomalias: insiders que nunca compraram antes e agora compram = sinal forte
    - Score = f(net_count, net_volume, anomaly_bonus)

    Retorna: (score, buy_count, sell_count, net_volume)
    """
    d30 = ref_date - timedelta(days=30)
    d90 = ref_date - timedelta(days=90)

    # Trades nos últimos 30 dias
    trades_30d = await db.execute(
        select(InsiderTrade).where(
            InsiderTrade.ticker == ticker,
            InsiderTrade.trade_date >= d30,
            InsiderTrade.trade_date <= ref_date,
        )
    )
    trades_30d = trades_30d.scalars().all()

    buy_count = sum(1 for t in trades_30d if t.trade_type == "Compra")
    sell_count = sum(1 for t in trades_30d if t.trade_type == "Venda")
    buy_volume = sum(t.volume for t in trades_30d if t.trade_type == "Compra")
    sell_volume = sum(t.volume for t in trades_30d if t.trade_type == "Venda")
    net_volume = buy_volume - sell_volume

    if buy_count == 0 and sell_count == 0:
        return (0.0, 0, 0, 0.0)

    # Score base: diferença proporcional entre compras e vendas
    total_count = buy_count + sell_count
    net_ratio = (buy_count - sell_count) / total_count  # -1 a +1
    base_score = net_ratio * 60  # -60 a +60

    # Bônus por volume (quanto maior o volume líquido, mais convicção)
    volume_total = buy_volume + sell_volume
    if volume_total > 0:
        volume_ratio = net_volume / volume_total  # -1 a +1
        volume_bonus = volume_ratio * 20  # -20 a +20
    else:
        volume_bonus = 0

    # Bônus por anomalia: insider que não comprava nos últimos 90 dias e agora compra
    anomaly_bonus = 0.0
    if buy_count > 0:
        buyers_30d = {t.insider_name for t in trades_30d if t.trade_type == "Compra"}
        for buyer in buyers_30d:
            # Verifica se esse insider comprou nos 60 dias anteriores ao período de 30d
            prior_buys = await db.execute(
                select(func.count()).where(
                    InsiderTrade.ticker == ticker,
                    InsiderTrade.insider_name == buyer,
                    InsiderTrade.trade_type == "Compra",
                    InsiderTrade.trade_date >= d90,
                    InsiderTrade.trade_date < d30,
                )
            )
            if prior_buys.scalar() == 0:
                anomaly_bonus += 10.0  # Novo comprador = sinal forte

    anomaly_bonus = min(anomaly_bonus, 20.0)  # Cap em +20

    score = _clamp(base_score + volume_bonus + anomaly_bonus)
    return (score, buy_count, sell_count, net_volume)


async def calc_short_component(
    db: AsyncSession, ticker: str, ref_date: date
) -> float:
    """
    Calcula componente de short interest.
    Aumento de short = negativo. Diminuição = positivo.
    """
    d30 = ref_date - timedelta(days=30)

    current = await db.execute(
        select(ShortInterest)
        .where(ShortInterest.ticker == ticker, ShortInterest.ref_date <= ref_date)
        .order_by(ShortInterest.ref_date.desc())
        .limit(1)
    )
    current = current.scalar_one_or_none()

    prior = await db.execute(
        select(ShortInterest)
        .where(ShortInterest.ticker == ticker, ShortInterest.ref_date <= d30)
        .order_by(ShortInterest.ref_date.desc())
        .limit(1)
    )
    prior = prior.scalar_one_or_none()

    if not current or not prior or prior.balance == 0:
        return 0.0

    change_pct = (current.balance - prior.balance) / prior.balance
    # Aumento de short = negativo, diminuição = positivo
    score = _clamp(-change_pct * 100)
    return score


async def calc_flow_component(
    db: AsyncSession, ref_date: date
) -> float:
    """
    Calcula componente de fluxo estrangeiro.
    Fluxo líquido positivo = bullish. Negativo = bearish.
    """
    d30 = ref_date - timedelta(days=30)

    flows = await db.execute(
        select(func.sum(InvestorFlow.net_volume)).where(
            InvestorFlow.investor_type.in_(["Estrangeiro", "ESTRANGEIRO", "Foreign"]),
            InvestorFlow.ref_date >= d30,
            InvestorFlow.ref_date <= ref_date,
        )
    )
    net_flow = flows.scalar() or 0.0

    # Normaliza para -100 a +100 (usando R$ 1bi como referência)
    score = _clamp((net_flow / 1_000_000_000) * 50)
    return score


async def calc_momentum_component(
    db: AsyncSession, ticker: str, ref_date: date
) -> float:
    """
    Calcula momentum técnico simples.
    Compara preço atual com médias móveis de 20 e 50 dias.
    """
    d60 = ref_date - timedelta(days=80)  # Margem para 50 dias úteis

    prices = await db.execute(
        select(StockPrice)
        .where(
            StockPrice.ticker == ticker,
            StockPrice.trade_date >= d60,
            StockPrice.trade_date <= ref_date,
        )
        .order_by(StockPrice.trade_date.asc())
    )
    prices = prices.scalars().all()

    if len(prices) < 10:
        return 0.0

    closes = [p.close_price for p in prices]
    current_price = closes[-1]

    # MA20
    ma20 = sum(closes[-20:]) / min(len(closes), 20) if len(closes) >= 5 else current_price
    # MA50
    ma50 = sum(closes[-50:]) / min(len(closes), 50) if len(closes) >= 10 else current_price

    # Score: acima das médias = positivo, abaixo = negativo
    score_ma20 = ((current_price / ma20) - 1) * 200 if ma20 > 0 else 0
    score_ma50 = ((current_price / ma50) - 1) * 100 if ma50 > 0 else 0

    score = _clamp((score_ma20 + score_ma50) / 2)
    return score


def determine_signal(total_score: float) -> str:
    """Converte score numérico em sinal textual."""
    if total_score >= 30:
        return "COMPRA"
    elif total_score <= -30:
        return "VENDA"
    return "NEUTRO"


async def calculate_score(
    db: AsyncSession, ticker: str, ref_date: date | None = None
) -> InsiderScore:
    """Calcula score completo para um ativo em uma data."""
    ref_date = ref_date or date.today()

    insider_score, buy_count, sell_count, net_volume = await calc_insider_component(
        db, ticker, ref_date
    )
    short_score = await calc_short_component(db, ticker, ref_date)
    flow_score = await calc_flow_component(db, ref_date)
    momentum_score = await calc_momentum_component(db, ticker, ref_date)

    total = (
        insider_score * WEIGHT_INSIDER
        + short_score * WEIGHT_SHORT
        + flow_score * WEIGHT_FLOW
        + momentum_score * WEIGHT_MOMENTUM
    )
    total = _clamp(total)
    signal = determine_signal(total)

    score_obj = InsiderScore(
        ticker=ticker,
        calc_date=ref_date,
        insider_score=round(insider_score, 2),
        short_score=round(short_score, 2),
        flow_score=round(flow_score, 2),
        momentum_score=round(momentum_score, 2),
        total_score=round(total, 2),
        signal=signal,
        insider_buy_count_30d=buy_count,
        insider_sell_count_30d=sell_count,
        insider_net_volume_30d=round(net_volume, 2),
    )
    return score_obj


async def calculate_all_scores(db: AsyncSession, ref_date: date | None = None) -> int:
    """Recalcula scores para todas as empresas."""
    ref_date = ref_date or date.today()

    companies = await db.execute(select(Company))
    companies = companies.scalars().all()

    count = 0
    for company in companies:
        try:
            score = await calculate_score(db, company.ticker, ref_date)
            db.add(score)
            count += 1
        except Exception as e:
            logger.error("Erro calculando score para %s: %s", company.ticker, e)

    await db.commit()
    logger.info("Calculados %d scores para %s", count, ref_date)
    return count
