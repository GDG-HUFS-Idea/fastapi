from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, DateTime, func
from sqlmodel import JSON, Field, SQLModel

from app.common.enums import SubscriptionPlan, UserRole


class User(SQLModel, table=True):
    __tablename__ = "user"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, nullable=False)
    name: str = Field(nullable=False)
    subscription_plan: SubscriptionPlan = Field(nullable=False)
    roles: List[UserRole] = Field(nullable=False, sa_type=JSON)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))
