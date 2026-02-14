"""Modelos de dados — cotações, insiders, scores."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Company(Base):
    """Empresa listada na B3."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(20))
    sector: Mapped[str | None] = mapped_column(String(100))
    segment: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class StockPrice(Base):
    """Cotação diária vinda do COTAHIST."""

    __tablename__ = "stock_prices"
    __table_args__ = (
        Index("ix_stock_prices_ticker_date", "ticker", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False)
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    num_trades: Mapped[int] = mapped_column(Integer, default=0)
    market_type: Mapped[int] = mapped_column(Integer, default=10)  # 10=vista, 12=exercicio opcoes, etc


class InsiderTrade(Base):
    """Negociação de insider (administrador/conselheiro) — dados CVM VLMO."""

    __tablename__ = "insider_trades"
    __table_args__ = (
        Index("ix_insider_trades_ticker_date", "ticker", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(20))
    insider_name: Mapped[str] = mapped_column(String(200), nullable=False)
    insider_role: Mapped[str | None] = mapped_column(String(100))
    trade_type: Mapped[str] = mapped_column(String(20), nullable=False)  # Compra / Venda
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    report_date: Mapped[date | None] = mapped_column(Date)
    intermediary: Mapped[str | None] = mapped_column(String(200))
    raw_data: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ShortInterest(Base):
    """Dados de empréstimo de ações (short interest) da B3."""

    __tablename__ = "short_interest"
    __table_args__ = (
        Index("ix_short_interest_ticker_date", "ticker", "ref_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    ref_date: Mapped[date] = mapped_column(Date, nullable=False)
    shares_lent: Mapped[float] = mapped_column(Float, default=0)
    balance: Mapped[float] = mapped_column(Float, default=0)
    avg_rate: Mapped[float] = mapped_column(Float, default=0)


class InvestorFlow(Base):
    """Fluxo por tipo de investidor (estrangeiro, institucional, PF)."""

    __tablename__ = "investor_flows"
    __table_args__ = (
        Index("ix_investor_flows_date", "ref_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ref_date: Mapped[date] = mapped_column(Date, nullable=False)
    investor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    buy_volume: Mapped[float] = mapped_column(Float, default=0)
    sell_volume: Mapped[float] = mapped_column(Float, default=0)
    net_volume: Mapped[float] = mapped_column(Float, default=0)


class InsiderScore(Base):
    """Score consolidado por ativo (-100 a +100)."""

    __tablename__ = "insider_scores"
    __table_args__ = (
        Index("ix_insider_scores_ticker_date", "ticker", "calc_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    calc_date: Mapped[date] = mapped_column(Date, nullable=False)
    insider_score: Mapped[float] = mapped_column(Float, default=0)
    short_score: Mapped[float] = mapped_column(Float, default=0)
    flow_score: Mapped[float] = mapped_column(Float, default=0)
    momentum_score: Mapped[float] = mapped_column(Float, default=0)
    total_score: Mapped[float] = mapped_column(Float, default=0)
    signal: Mapped[str] = mapped_column(String(10), default="NEUTRO")  # COMPRA / NEUTRO / VENDA
    insider_buy_count_30d: Mapped[int] = mapped_column(Integer, default=0)
    insider_sell_count_30d: Mapped[int] = mapped_column(Integer, default=0)
    insider_net_volume_30d: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
