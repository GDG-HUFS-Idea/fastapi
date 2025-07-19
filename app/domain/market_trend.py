from datetime import datetime
from typing import Optional
from sqlmodel import BIGINT, Column, DateTime, Field, SQLModel, func

from app.common.enums import Currency, MarketScope


class MarketTrend(SQLModel, table=True):
    __tablename__ = "market_trend"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: int = Field(foreign_key="market_research.id")
    scope: MarketScope = Field(nullable=False)
    year: int = Field(nullable=False)
    size: int = Field(nullable=False, sa_type=BIGINT)
    currency: Currency = Field(nullable=False)
    growth_rate: float = Field(default=None, decimal_places=2)
    source: str = Field(nullable=False)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
