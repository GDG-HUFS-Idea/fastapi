from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, func
from sqlmodel import Column, Field, SQLModel


class UserAgreement(SQLModel, table=True):
    __tablename__ = "user_agreement"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    term_id: int = Field(foreign_key="term.id")
    is_agreed: bool = Field(nullable=False)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
