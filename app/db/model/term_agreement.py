from datetime import datetime
from typing import Optional
from sqlmodel import Column, DateTime, Field, ForeignKey, SQLModel, func


class TermAgreement(SQLModel, table=True):
    __tablename__ = "term_agreement"  # type: ignore

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    user_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "user.id",
                ondelete="CASCADE",
            )
        )
    )
    term_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "term.id",
                ondelete="CASCADE",
            )
        )
    )

    has_agreed: bool

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
