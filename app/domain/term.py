from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

from app.common.enums import TermType


class Term(SQLModel, table=True):
    __tablename__ = "term"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    type: TermType = Field(unique=True, nullable=False)
    is_required: bool = Field(nullable=False)
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)
    version: str = Field(nullable=False)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
