from datetime import datetime
from typing import List, Optional
from sqlmodel import JSON, Column, DateTime, Field, SQLModel, func

from app.util.enum import PlanType, UserRole


class User(SQLModel, table=True):
    __tablename__ = "user"  # type: ignore

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    name: str
    email: str = Field(unique=True)
    roles: List[UserRole] = Field(
        default=[UserRole.GENERAL],
        sa_type=JSON,
    )
    plan: PlanType = Field(default=PlanType.FREE)

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
