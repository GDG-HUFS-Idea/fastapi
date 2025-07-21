from typing import Optional
from sqlmodel import BIGINT, Field, SQLModel

from app.common.enums import Currency, MarketScope


class RevenueBenchmark(SQLModel, table=True):
    __tablename__ = "revenue_benchmark"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: int = Field(foreign_key="market_research.id")
    scope: MarketScope = Field(nullable=False)
    average_revenue: int = Field(nullable=False, sa_type=BIGINT)
    currency: Currency = Field(nullable=False)
    source: str = Field(nullable=False)
