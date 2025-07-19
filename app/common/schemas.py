from typing import List, Optional
from pydantic import BaseModel

from app.common.enums import Currency


class KSICItem(BaseModel):
    code: str
    name: str


class KSICHierarchy(BaseModel):
    large: KSICItem
    medium: KSICItem
    small: KSICItem
    detail: KSICItem


class SimilarService(BaseModel):
    name: str
    description: str
    logo_url: str
    website: str
    tags: List[str]
    summary: str


class SupportProgram(BaseModel):
    name: str
    organizer: str
    url: str
    start_date: str
    end_date: str


class TargetMarketActivity(BaseModel):
    online: str


class TargetMarketTouchpoint(BaseModel):
    online: str
    offline: str


class TargetMarket(BaseModel):
    segment: str
    reason: str
    value_prop: str
    activities: TargetMarketActivity
    touchpoints: TargetMarketTouchpoint


class MarketingPlanPhase(BaseModel):
    pre: str
    launch: str
    growth: str


class MarketingPlan(BaseModel):
    approach: str
    channels: List[str]
    messages: List[str]
    budget: int
    kpis: List[str]
    phase: MarketingPlanPhase


class BusinessModelValueProposition(BaseModel):
    main: str
    detail: str


class BusinessModelPriority(BaseModel):
    name: str
    description: str


class BusinessModel(BaseModel):
    summary: str
    value_proposition: BusinessModelValueProposition
    revenue_stream: str
    priorities: List[BusinessModelPriority]
    break_even_point: str


class Limitation(BaseModel):
    category: str
    detail: str
    impact: str
    mitigation: str


class TeamRequirement(BaseModel):
    priority: str
    position: str
    skill: str
    tasks: str


class MarketTrend(BaseModel):
    year: int
    size: int
    growth_rate: Optional[float]
    currency: Currency
    source: str


class RevenueBenchmark(BaseModel):
    average_revenue: int
    currency: Currency
    source: str
