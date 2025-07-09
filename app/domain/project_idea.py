from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column
from sqlmodel import JSON, TEXT, DateTime, Field, SQLModel, func


class ProjectIdea(SQLModel, table=True):
    __tablename__ = "project_idea"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", unique=True)
    problem: str = Field(nullable=False, sa_type=TEXT)
    solution: str = Field(nullable=False, sa_type=TEXT)
    issues: List[str] = Field(nullable=False, sa_type=JSON)
    motivation: str = Field(nullable=False)
    features: List[str] = Field(nullable=False, sa_type=JSON)
    method: str = Field(nullable=False)
    deliverable: str = Field(nullable=False)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))
