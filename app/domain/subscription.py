from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlmodel import Column, DateTime, Field, SQLModel

from app.common.enums import SubscriptionPlan, SubscriptionStatus


class Subscription(SQLModel, table=True):
    __tablename__ = "subscription"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    plan: SubscriptionPlan = Field(nullable=False)
    status: SubscriptionStatus = Field(nullable=False)
    started_at: datetime = Field(nullable=False)
    expires_at: datetime = Field(nullable=False)
    cancelled_at: Optional[datetime] = None
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
