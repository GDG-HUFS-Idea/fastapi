from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from sqlalchemy import Column, func
from sqlmodel import DateTime, Field, SQLModel

from app.common import schemas


class MarketResearch(SQLModel, table=True):
    __tablename__ = "market_research"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    ksic_hierarchy: schemas.KSICHierarchy = Field(nullable=False, sa_type=JSONB)
    market_score: int = Field(default=None, ge=1, le=100)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
