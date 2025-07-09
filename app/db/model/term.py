from datetime import datetime
from typing import Optional
from sqlmodel import Column, DateTime, Field, SQLModel, Text, func

from app.util.enum import TermType


class Term(SQLModel, table=True):
    __tablename__ = "term"  # type: ignore

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    type: TermType
    is_required: bool
    title: str
    content: str = Field(sa_type=Text)

    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
        ),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
