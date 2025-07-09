from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, func

from app.common.enums import ProjectStatus


class Project(SQLModel, table=True):
    __tablename__ = "project"  # type: ignore

    id: Optional[int] = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key="user.id")
    name: str = Field(nullable=False)
    status: ProjectStatus = Field(nullable=False)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))
