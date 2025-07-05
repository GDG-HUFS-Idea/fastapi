from datetime import datetime
from typing import Optional
from sqlmodel import JSON, Column, DateTime, Field, SQLModel, func


class DeletionLog(SQLModel, table=True):
    __tablename__ = "deletion_log"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    deleted_by: int
    table_name: str
    record_id: int
    record_data: dict = Field(sa_column=Column(JSON))
    deleted_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))
