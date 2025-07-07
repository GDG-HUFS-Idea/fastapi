from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, func
from sqlmodel import DateTime, Field, SQLModel


class _KSICItem(BaseModel):
    code: str
    name: str


class _KSICHierarchy(BaseModel):
    large: _KSICItem
    medium: _KSICItem
    small: _KSICItem
    detail: _KSICItem


class MarketResearch(SQLModel, table=True):
    __tablename__ = "market_research"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    ksic_hierarchy: _KSICHierarchy = Field(nullable=False, sa_type=JSONB)
    market_score: Optional[int] = Field(default=None, ge=1, le=100)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    @classmethod
    def create_from_dict(
        cls,
        data: Dict[str, Any],
    ) -> 'MarketResearch':
        return cls(**data)

    @field_validator('ksic_hierarchy', mode='before')
    @classmethod
    def validate_ksic_hierarchy(cls, v):
        if isinstance(v, dict):
            return _KSICHierarchy(**v)
        return v
