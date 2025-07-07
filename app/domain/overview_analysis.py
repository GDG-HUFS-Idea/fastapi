from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
from sqlalchemy import JSON, Column, func
from sqlmodel import DateTime, Field, SQLModel

from app.common.enums import RiskCategory


class _SimilarService(BaseModel):
    name: str
    description: str
    logo_url: str
    website: str
    tags: List[str]
    summary: str


class _SupportProgram(BaseModel):
    name: str
    organizer: str
    url: str
    start_date: str
    end_date: str


class _Activity(BaseModel):
    online: List[str]


class _Touchpoint(BaseModel):
    online: List[str]
    offline: List[str]


class _TargetMarket(BaseModel):
    segment: str
    reasons: List[str]
    value_props: List[str]
    activities: _Activity
    touchpoints: _Touchpoint


class _Phase(BaseModel):
    pre: str
    launch: str
    growth: str


class _MarketingPlan(BaseModel):
    approach: str
    channels: List[str]
    messages: List[str]
    budget: int
    kpis: List[str]
    phase: _Phase


class _ValueProposition(BaseModel):
    main: str
    detail: List[str]


class _Priority(BaseModel):
    name: str
    description: str


class _BusinessModel(BaseModel):
    summary: str
    value_proposition: _ValueProposition
    revenue_stream: str
    priorities: List[_Priority]
    break_even_point: str


class _Limitation(BaseModel):
    category: RiskCategory
    detail: str
    impact: str
    mitigation: str


class _TeamRequirement(BaseModel):
    priority: str
    position: str
    skill: str
    tasks: str


class _KSICItem(BaseModel):
    code: str
    name: str


class _KSICHierarchy(BaseModel):
    large: _KSICItem
    medium: _KSICItem
    small: _KSICItem
    detail: _KSICItem


class OverviewAnalysis(SQLModel, table=True):
    __tablename__ = "overview_analysis"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int = Field(foreign_key="project_idea.id", index=True)
    ksic_hierarchy: _KSICHierarchy = Field(nullable=False, sa_type=JSONB)
    evaluation: str = Field(nullable=False)
    similarity_score: int = Field(nullable=False, ge=1, le=100)
    risk_score: int = Field(nullable=False, ge=1, le=100)
    opportunity_score: int = Field(nullable=False, ge=1, le=100)
    similar_services: List[_SimilarService] = Field(nullable=False, sa_type=JSON)
    support_programs: List[_SupportProgram] = Field(nullable=False, sa_type=JSON)
    target_markets: List[_TargetMarket] = Field(nullable=False, sa_type=JSON)
    marketing_plans: _MarketingPlan = Field(nullable=False, sa_type=JSON)
    business_model: Optional[_BusinessModel] = Field(default=None, sa_type=JSON)
    opportunities: List[str] = Field(nullable=False, sa_type=JSON)
    limitations: List[_Limitation] = Field(nullable=False, sa_type=JSON)
    team_requirements: List[_TeamRequirement] = Field(nullable=False, sa_type=JSON)
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
            return _KSICHierarchy(**v)
        return v

    @field_validator('similar_services', mode='before')
    @classmethod
    def validate_similar_services(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [_SimilarService(**item) for item in v]
        return v

    @field_validator('support_programs', mode='before')
    @classmethod
    def validate_support_programs(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [_SupportProgram(**item) for item in v]
        return v

    @field_validator('target_markets', mode='before')
    @classmethod
    def validate_target_markets(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [_TargetMarket(**item) for item in v]
        return v

    @field_validator('marketing_plans', mode='before')
    @classmethod
    def validate_marketing_plans(cls, v):
        if isinstance(v, dict):
            return _MarketingPlan(**v)
        return v

    @field_validator('business_model', mode='before')
    @classmethod
    def validate_business_model(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            return _BusinessModel(**v)
        return v

    @field_validator('limitations', mode='before')
    @classmethod
    def validate_limitations(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [_Limitation(**item) for item in v]
        return v

    @field_validator('team_requirements', mode='before')
    @classmethod
    def validate_team_requirements(cls, v):
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [_TeamRequirement(**item) for item in v]
        return v
