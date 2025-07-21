from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional, Dict, Any
from pydantic import field_validator
from sqlalchemy import JSON, Column, func
from sqlmodel import DateTime, Field, SQLModel

from app.common import schemas


class OverviewAnalysis(SQLModel, table=True):
    __tablename__ = "overview_analysis"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int = Field(foreign_key="project_idea.id", index=True)
    ksic_hierarchy: schemas.KSICHierarchy = Field(nullable=False, sa_type=JSONB)
    evaluation: str = Field(nullable=False)
    similarity_score: int = Field(nullable=False, ge=1, le=100)
    risk_score: int = Field(nullable=False, ge=1, le=100)
    opportunity_score: int = Field(nullable=False, ge=1, le=100)
    similar_services: List[schemas.SimilarService] = Field(nullable=False, sa_type=JSON)
    support_programs: List[schemas.SupportProgram] = Field(nullable=False, sa_type=JSON)
    target_markets: List[schemas.TargetMarket] = Field(nullable=False, sa_type=JSON)
    marketing_plans: schemas.MarketingPlan = Field(nullable=False, sa_type=JSON)
    business_model: schemas.BusinessModel = Field(default=None, sa_type=JSON)
    opportunities: List[str] = Field(nullable=False, sa_type=JSON)
    limitations: List[schemas.Limitation] = Field(nullable=False, sa_type=JSON)
    team_requirements: List[schemas.TeamRequirement] = Field(nullable=False, sa_type=JSON)
    created_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    @classmethod
    def create_from_dict(
        cls,
        data: Dict[str, Any],
    ) -> 'OverviewAnalysis':
        return cls(**data)

    @field_validator('ksic_hierarchy', mode='before')
    @classmethod
    def validate_ksic_hierarchy(cls, v):
        if isinstance(v, dict):
            return schemas.KSICHierarchy(**v)
        return v

    @field_validator('similar_services', mode='before')
    @classmethod
    def validate_similar_services(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [schemas.SimilarService(**item) for item in v]
        return v

    @field_validator('support_programs', mode='before')
    @classmethod
    def validate_support_programs(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [schemas.SupportProgram(**item) for item in v]
        return v

    @field_validator('target_markets', mode='before')
    @classmethod
    def validate_target_markets(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [schemas.TargetMarket(**item) for item in v]
        return v

    @field_validator('marketing_plans', mode='before')
    @classmethod
    def validate_marketing_plans(cls, v):
        if isinstance(v, dict):
            return schemas.MarketingPlan(**v)
        return v

    @field_validator('business_model', mode='before')
    @classmethod
    def validate_business_model(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            return schemas.BusinessModel(**v)
        return v

    @field_validator('limitations', mode='before')
    @classmethod
    def validate_limitations(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [schemas.Limitation(**item) for item in v]
        return v

    @field_validator('team_requirements', mode='before')
    @classmethod
    def validate_team_requirements(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [schemas.TeamRequirement(**item) for item in v]
        return v
