"""
Pydantic schemas for API request/response validation
"""

from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class StockPriceResponse(BaseModel):
    """Single price record"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")

    model_config = ConfigDict(from_attributes=True)


class StockResponse(BaseModel):
    """Stock information"""
    id: int
    symbol: str = Field(..., description="Stock ticker symbol (e.g., PETR4)")
    name: str = Field(..., description="Company name")
    price: float = Field(..., description="Current price")
    change_percent: float = Field(..., description="Price change percentage")
    volume: int = Field(..., description="Trading volume")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class StockWithPricesResponse(StockResponse):
    """Stock with price history"""
    prices: list[StockPriceResponse] = Field(default_factory=list)


class StockListResponse(BaseModel):
    """Paginated list of stocks"""
    total: int = Field(..., description="Total number of stocks")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    stocks: list[StockResponse] = Field(..., description="List of stocks")


class PriceHistoryResponse(BaseModel):
    """Price history for a stock"""
    symbol: str = Field(..., description="Stock ticker symbol")
    start_date: Optional[str] = Field(None, description="Start date of range")
    end_date: Optional[str] = Field(None, description="End date of range")
    total: int = Field(..., description="Total number of price records")
    prices: list[StockPriceResponse] = Field(..., description="Price records")
