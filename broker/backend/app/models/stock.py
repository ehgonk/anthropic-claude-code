from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float, default=0.0)
    change_percent: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    prices: Mapped[list["StockPrice"]] = relationship(back_populates="stock", cascade="all, delete-orphan")


class StockPrice(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (
        UniqueConstraint('stock_id', 'date', name='uq_stock_date'),
        Index('ix_stock_prices_stock_id_date', 'stock_id', 'date'),
        Index('ix_stock_prices_date', 'date'),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"))
    symbol: Mapped[str] = mapped_column(String(10))
    date: Mapped[str] = mapped_column(String(10))  # Format: YYYY-MM-DD
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[str] = mapped_column(String(30), nullable=True)

    # Relationship
    stock: Mapped["Stock"] = relationship(back_populates="prices")
