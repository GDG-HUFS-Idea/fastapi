from __future__ import annotations
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# ---------- 공통 타입 ----------
class MarketType(str, Enum):
    MASS = "mass_market"
    NICHE = "niche_market"
    SEGMENTED = "segmented_market"
    MULTI_SIDED = "multi_sided_platform"


class RelationshipType(str, Enum):
    PERSONAL_ASSISTANCE = "personal_assistance"
    SELF_SERVICE = "self_service"
    AUTOMATED_SERVICE = "automated_service"
    COMMUNITY = "community"
    CO_CREATION = "co_creation"


class RevenueType(str, Enum):
    SALES = "sales_revenue"
    SUBSCRIPTION = "subscription_fee"
    ADVERTISEMENT = "advertisement"
    COMMISSION = "transaction_fee"
    LICENSING = "licensing"
    OTHER = "other"


class CostType(str, Enum):
    FIXED = "fixed_cost"
    VARIABLE = "variable_cost"


# ---------- 1. Customer Segment ----------
class CustomerSegmentInput(BaseModel):
    service_purpose: str = Field(..., description="왜 꼭 이 서비스여야 하는지에 대한 목적성/필요성")
    validation_activities: Optional[str] = Field(None, description="A/B 테스트, 인터뷰 요약 등 고객 검증 활동")
    user_characteristics: Optional[str] = Field(None, description="확보된 사용자의 특성/사용 맥락")


class CustomerNeedItem(BaseModel):
    segment: str = Field(..., description="고객군 이름 또는 분류 기준")
    pain: Optional[str] = Field(None, description="겪는 불편")
    need: Optional[str] = Field(None, description="니즈")
    opportunity: Optional[str] = Field(None, description="기회/인사이트")


class CustomerSegmentOutput(BaseModel):
    target_market: str = Field(..., description="타겟 시장")
    customer_groups: List[str] = Field(..., description="핵심 고객 집단 리스트")
    market_type: MarketType = Field(..., description="시장 유형(매스, 틈새, 세분화, 멀티사이드)")
    reason_for_market_type: str = Field(..., description="선택한 시장 유형의 이유")
    common_needs_table: List[CustomerNeedItem] = Field(..., description="고객군별 불편/니즈/기회 요약 테이블")


# ---------- 2. Value Proposition ----------
class ValuePropositionInput(BaseModel):
    unique_features: Optional[str] = Field(None, description="독특한 기능/경험")
    memorable_feedback: Optional[str] = Field(None, description="인상 깊었던 사용자 피드백")
    emotional_or_practical_value: Optional[str] = Field(None, description="감정적/실용적 가치")


class CompetitorDiffItem(BaseModel):
    factor: str = Field(..., description="차별 요소 항목(가격, 효율 등)")
    explanation: str = Field(..., description="차별 이유 설명")


class ValuePropositionOutput(BaseModel):
    core_value_one_liner: str = Field(..., description="핵심 가치 한줄 정의")
    problem_solution_flow: str = Field(..., description="고객 문제 → 해결 방식 흐름")
    competitor_diff: List[CompetitorDiffItem] = Field(..., description="경쟁사 대비 차별 요소")
    emotional_benefit_summary: Optional[str] = Field(None, description="감정적 혜택 요약")


# ---------- 3. Channels ----------
class ChannelsInput(BaseModel):
    performance_metrics: Optional[str] = Field(None, description="MAU, WAU 등의 지표")
    main_touchpoints: Optional[str] = Field(None, description="주요 접점(랜딩페이지, 앱스토어 등)")
    tried_marketing_channels: Optional[str] = Field(None, description="사용해본 마케팅 채널 + 성과 데이터")
    sales_distribution: Optional[str] = Field(None, description="판매/유통 방식")


class ChannelStageItem(BaseModel):
    stage: str = Field(..., description="인지/고려/구매/유지/추천 중 하나")
    channels: List[str] = Field(..., description="해당 단계에서 사용하는 채널 목록")
    strategy_or_roi: Optional[str] = Field(None, description="전략 또는 ROI 요약")


class ChannelsOutput(BaseModel):
    journey_channels: List[ChannelStageItem] = Field(..., description="고객 여정 단계별 채널 정리")
    improvement_points: Optional[str] = Field(None, description="개선해야 할 부분")
    convenience_vs_competition: Optional[str] = Field(None, description="대체재 대비 편리/저렴/효율성 등 비교")


# ---------- 4. Customer Relationships ----------
class CustomerRelationshipsInput(BaseModel):
    communication_methods: Optional[str] = Field(None, description="현재 고객과 소통 방식")
    retention_methods: Optional[str] = Field(None, description="리텐션을 높이기 위한 방법")
    recent_complaints: Optional[str] = Field(None, description="최근 불만과 대응")
    customer_info_management: Optional[str] = Field(None, description="고객 정보 정리 방식")


class RelationshipItem(BaseModel):
    relationship_type: RelationshipType = Field(..., description="관계 유형")
    description: str = Field(..., description="유형 설명/구현 방식")


class CustomerRelationshipsOutput(BaseModel):
    relationship_strategies: List[RelationshipItem] = Field(..., description="관계 유지 방식 목록")
    loyalty_strategy: Optional[str] = Field(None, description="고객 충성도/팬덤 전략")


# ---------- 5. Revenue Streams ----------
class RevenueStreamsInput(BaseModel):
    current_revenue_model: Optional[str] = Field(None, description="현재 수익 창출 방식")
    payment_timing: Optional[str] = Field(None, description="사용자가 결제하는 시점")
    pricing_policy: Optional[str] = Field(None, description="가격 정책(무료/유료, 정액/종량 등)")
    revenue_amount: Optional[str] = Field(None, description="이미 벌고 있는 금액과 측정 이유")


class RevenueItem(BaseModel):
    revenue_type: RevenueType = Field(..., description="수익 유형")
    detail: str = Field(..., description="가격/수수료율 등 상세 구조")
    reason: Optional[str] = Field(None, description="그 가격을 설정한 이유")


class RevenueStreamsOutput(BaseModel):
    revenue_flows: List[RevenueItem] = Field(..., description="수익 흐름 구조 상세")
    expansion_ideas: Optional[str] = Field(None, description="향후 확장 가능한 수익원 아이디어")


# ---------- 6. Key Resources ----------
class KeyResourcesInput(BaseModel):
    owned_resources: Optional[str] = Field(None, description="보유 중인 자원(기술, 인력 등)")
    planned_resources: Optional[str] = Field(None, description="보유 예정 자원/시설")
    lacking_or_outsourced: Optional[str] = Field(None, description="부족/외부 의존 자원")


class ResourceItem(BaseModel):
    category: str = Field(..., description="자원 유형(기술, 인적, 재무 등)")
    name: str = Field(..., description="자원명/설명")
    link_to_value_or_relationship: Optional[str] = Field(None, description="가치제안/고객관계와의 연결")


class KeyResourcesOutput(BaseModel):
    essential_resources: List[ResourceItem] = Field(..., description="필수 자원 목록")
    short_mid_long_strategy: Optional[str] = Field(None, description="단기/중장기 자원 확보 전략")


# ---------- 7. Key Activities ----------
class KeyActivitiesInput(BaseModel):
    limited_tasks_for_value: Optional[str] = Field(None, description="가치제안을 위한 제한된/핵심 업무")
    meeting_customer_channels: Optional[str] = Field(None, description="현재 고객을 만나는 수단")


class ActivityItem(BaseModel):
    name: str = Field(..., description="주요 활동명")
    order: int = Field(..., description="수행 순서")
    criticality: Optional[str] = Field(None, description="필수 정도(정성 또는 수치화)")


class KeyActivitiesOutput(BaseModel):
    essential_activities: List[ActivityItem] = Field(..., description="핵심 업무 목록")
    relationship_activities: Optional[str] = Field(None, description="고객 관계 유지에 중요한 활동")


# ---------- 8. Key Partnerships ----------
class KeyPartnershipsInput(BaseModel):
    planned_collaborations: Optional[str] = Field(None, description="협업 예정 기술/아이템")
    ongoing_collaborations: Optional[str] = Field(None, description="이미 진행 중인 협업")


class PartnershipItem(BaseModel):
    partner_type: str = Field(..., description="파트너 유형(전략적 동맹, 코피티션 등)")
    purpose: str = Field(..., description="파트너십 목적")
    business_link: Optional[str] = Field(None, description="사업 연결 구조 요약")


class KeyPartnershipsOutput(BaseModel):
    partnerships: List[PartnershipItem] = Field(..., description="주요 파트너 목록")
    overall_structure: Optional[str] = Field(None, description="비즈니스 모델 작동에 필요한 협력 구조 설명")


# ---------- 9. Cost Structure ----------
class CostStructureInput(BaseModel):
    funding_plan: Optional[str] = Field(None, description="개발/유지/보수 자금 조달 계획")
    # 삭제 여부 논의된 '현재까지 사용된 자금'은 옵션으로 유지 가능
    spent_budget: Optional[str] = Field(None, description="현재까지 사용된 자금 (선택)")


class CostItem(BaseModel):
    name: str = Field(..., description="비용 항목명")
    cost_type: CostType = Field(..., description="고정/변동")
    scale: Optional[str] = Field(None, description="추정 규모 또는 수치")


class CostStructureOutput(BaseModel):
    cost_items: List[CostItem] = Field(..., description="주요 비용 항목 및 규모")
    notes: Optional[str] = Field(None, description="비고 또는 추가 설명")


# ---------- 통합 요청/응답 모델 ----------
class Blocks9Input(BaseModel):
    customer_segment: Optional[CustomerSegmentInput]
    value_proposition: Optional[ValuePropositionInput]
    channels: Optional[ChannelsInput]
    customer_relationships: Optional[CustomerRelationshipsInput]
    revenue_streams: Optional[RevenueStreamsInput]
    key_resources: Optional[KeyResourcesInput]
    key_activities: Optional[KeyActivitiesInput]
    key_partnerships: Optional[KeyPartnershipsInput]
    cost_structure: Optional[CostStructureInput]


class Blocks9Output(BaseModel):
    customer_segment: Optional[CustomerSegmentOutput]
    value_proposition: Optional[ValuePropositionOutput]
    channels: Optional[ChannelsOutput]
    customer_relationships: Optional[CustomerRelationshipsOutput]
    revenue_streams: Optional[RevenueStreamsOutput]
    key_resources: Optional[KeyResourcesOutput]
    key_activities: Optional[KeyActivitiesOutput]
    key_partnerships: Optional[KeyPartnershipsOutput]
    cost_structure: Optional[CostStructureOutput]


class MissingField(BaseModel):
    block: str = Field(..., description="누락된 블록 이름")
    fields: List[str] = Field(..., description="필수 입력 중 누락된 필드 목록")


class Blocks9CheckResponse(BaseModel):
    """
    분석 전 입력 검증 결과.
    - missing: 누락된 필드가 있으면 목록 반환
    - ready: 모두 준비되면 True
    """
    ready: bool = Field(..., description="모든 블록이 준비되었는지 여부")
    missing: List[MissingField] = Field(default_factory=list, description="블록별 누락 필드 리스트")
