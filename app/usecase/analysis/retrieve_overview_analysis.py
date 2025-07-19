import logging
from typing import List
from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.common import schemas
from app.repository.market_research import MarketResearchRepository
from app.repository.market_trend import MarketTrendRepository
from app.repository.overview_analysis import OverviewAnalysisRepository
from app.repository.project import ProjectRepository
from app.repository.revenue_benchmark import RevenueBenchmarkRepository
from app.service.auth.jwt import Payload
from app.common.exceptions import ForbiddenException, NotFoundException, RepositoryError, UsecaseException, InternalServerException

logger = logging.getLogger(__name__)


class RetrieveOverviewAnalysisUsecaseDTO(BaseModel):
    project_id: int = Field(Query(ge=1, description="조회할 프로젝트 ID"))

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "project_id": 1,
                }
            ]
        }
    )


class _Score(BaseModel):
    market: int
    simliar_service: int
    risk: int
    opportunity: int


class _MarketTrend(BaseModel):
    year: int
    size: float
    growth_rate: float
    currency: str
    source: str


class _MarketTrends(BaseModel):
    domestic: List[_MarketTrend]
    global_: List[_MarketTrend] = Field(alias="global")


class _RevenueBenchmark(BaseModel):
    average_revenue: float
    currency: str
    source: str


class _RevenueBenchmarks(BaseModel):
    domestic: _RevenueBenchmark
    global_: _RevenueBenchmark = Field(alias="global")


class RetrieveOverviewAnalysisUsecaseResponse(BaseModel):
    ksic_hierarchy: schemas.KSICHierarchy
    evaluation: str
    score: _Score
    market_trends: _MarketTrends
    revenue_becnhmarks: _RevenueBenchmarks
    similar_services: List[schemas.SimilarService]
    support_programs: List[schemas.SupportProgram]
    target_markets: List[schemas.TargetMarket]
    limitations: List[schemas.Limitation]
    marketing_plan: schemas.MarketingPlan
    business_model: schemas.BusinessModel
    opportunities: List[str]
    team_requirements: List[schemas.TeamRequirement]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ksic_hierarchy": {
                        "large": {"code": "G", "name": "도매 및 소매업"},
                        "medium": {"code": "G46", "name": "기타 도매업"},
                        "small": {"code": "G466", "name": "기타 전문 도매업"},
                        "detail": {"code": "G4669", "name": "기타 전문 도매업 외 기타"},
                    },
                    "evaluation": "안전한 미래를 위한 준비가 강점이 될 수 있고, 법률적 규제 부분에 위험성을 가지고 있습니다. 실현 가능성은 높음이며, 지속 가능성은 높음입니다. 시장 진출 타이밍은 현재가 적절해 보입니다.",
                    "score": {"market": 80, "simliar_service": 70, "risk": 60, "opportunity": 75},
                    "market_trends": {
                        "domestic": [
                            {"year": 2025, "size": 3600000.0, "growth_rate": 12.5, "currency": "KRW", "source": "한국무역협회"},
                            {"year": 2024, "size": 3200000.0, "growth_rate": 14.29, "currency": "KRW", "source": "한국무역협회"},
                            {"year": 2023, "size": 2800000.0, "growth_rate": 12.0, "currency": "KRW", "source": "한국무역협회"},
                            {"year": 2022, "size": 2500000.0, "growth_rate": 13.64, "currency": "KRW", "source": "한국무역협회"},
                            {"year": 2021, "size": 2200000.0, "growth_rate": 10.0, "currency": "KRW", "source": "한국무역협회"},
                        ],
                        "global": [
                            {
                                "year": 2025,
                                "size": 202320000000.0,
                                "growth_rate": 8.26,
                                "currency": "USD",
                                "source": "Verified Market Reports",
                            },
                            {
                                "year": 2024,
                                "size": 137580000000.0,
                                "growth_rate": 11.4,
                                "currency": "USD",
                                "source": "Verified Market Reports",
                            },
                            {
                                "year": 2023,
                                "size": 124500000000.0,
                                "growth_rate": 5.0,
                                "currency": "USD",
                                "source": "Verified Market Reports",
                            },
                            {
                                "year": 2022,
                                "size": 110000000000.0,
                                "growth_rate": 10.0,
                                "currency": "USD",
                                "source": "Verified Market Reports",
                            },
                            {
                                "year": 2021,
                                "size": 100000000000.0,
                                "growth_rate": 5.3,
                                "currency": "USD",
                                "source": "Verified Market Reports",
                            },
                        ],
                    },
                    "revenue_becnhmarks": {
                        "domestic": {"average_revenue": 2500000.0, "currency": "USD", "source": "한국무역협회 및 Verified Market Reports"},
                        "global": {
                            "average_revenue": 124500000000.0,
                            "currency": "USD",
                            "source": "한국무역협회 및 Verified Market Reports",
                        },
                    },
                    "similar_services": [
                        {
                            "name": "Ready America",
                            "description": "Ready America는 응급 백팩과 파워 스테이션 등을 판매하는 재난 용품 전문업체입니다. 자연재해 대비를 위한 다양한 제품을 제공하며, 최근 몇 년간 매출이 크게 증가했습니다. 이들은 고객의 안전을 최우선으로 생각하며, 다양한 재난 상황에 대비할 수 있는 제품을 지속적으로 개발하고 있습니다.",
                            "logo_url": "",
                            "website": "https://www.readyamerica.com",
                            "tags": ["재난 대비", "응급 백팩", "파워 스테이션", "자연재해", "안전 용품"],
                            "summary": "재난 대비 용품 판매",
                        },
                        {
                            "name": "Atlas Survival Shelters",
                            "description": "Atlas Survival Shelters는 스톰 쉘터와 벙커를 제작하는 회사로, 자연재해 대비를 위한 인테리어 제품도 제공합니다. 이들은 고객의 안전을 보장하기 위해 다양한 안전 시설을 제공하며, 고객의 요구에 맞춘 맞춤형 솔루션을 제공합니다.",
                            "logo_url": "",
                            "website": "https://www.atlassurvivalshelters.com",
                            "tags": ["재난 대비", "벙커", "스톰 쉘터", "안전 시설", "구조물"],
                            "summary": "재난 대비 시설 제공",
                        },
                        {
                            "name": "FEMA",
                            "description": "FEMA는 미국의 재난 관리 기관으로, 자연재해 대비를 위한 필수품 목록을 제공합니다. 이 목록은 재난 상황에서 필요한 물품을 준비하는 데 도움을 줍니다. FEMA는 또한 재난 발생 시 신속한 대응을 위한 다양한 프로그램을 운영하고 있습니다.",
                            "logo_url": "",
                            "website": "https://www.fema.gov",
                            "tags": ["재난 대비", "필수품 목록", "정부 기관", "안전 정보", "재난 관리"],
                            "summary": "재난 대비 정보 제공",
                        },
                        {
                            "name": "REI",
                            "description": "REI는 야외 활동 용품을 판매하는 회사로, 자연재해 대비를 위한 응급 키트와 같은 제품도 제공합니다. 이들은 고객의 안전과 편의를 고려하여 다양한 제품을 제공하며, 야외 활동을 즐기는 고객들에게 적합한 솔루션을 제공합니다.",
                            "logo_url": "",
                            "website": "https://www.rei.com",
                            "tags": ["야외 활동", "응급 키트", "재난 대비", "안전 용품", "레저"],
                            "summary": "야외 활동 용품 판매",
                        },
                        {
                            "name": "Home Depot",
                            "description": "Home Depot은 가정 및 건축 용품을 판매하는 대형 유통업체로, 자연재해 대비를 위한 발전기와 같은 제품도 제공합니다. 이들은 고객의 다양한 요구를 충족시키기 위해 다양한 제품을 제공하며, 안전과 편리함을 동시에 고려한 솔루션을 제공합니다.",
                            "logo_url": "",
                            "website": "https://www.homedepot.com",
                            "tags": ["재난 대비", "발전기", "가정 용품", "안전 장비", "비상 용품"],
                            "summary": "재난 대비 용품 판매",
                        },
                    ],
                    "support_programs": [
                        {
                            "name": "물 재해 대비 체계 구축 지원",
                            "organizer": "한국 정부",
                            "url": "",
                            "start_date": "상시 또는 분기별 공고",
                            "end_date": "상시 또는 분기별 공고",
                        },
                        {
                            "name": "중소벤처기업부 기술창업 지원",
                            "organizer": "중소벤처기업부",
                            "url": "",
                            "start_date": "연 2회 (상반기, 하반기)",
                            "end_date": "연 2회 (상반기, 하반기)",
                        },
                    ],
                    "target_markets": [
                        {
                            "segment": "30-40대 직장인",
                            "reason": "이 세그먼트는 자연재해에 대한 인식이 높고, 가족과 자산을 보호하려는 경향이 강합니다.",
                            "value_prop": "안전, 가족 보호, 재난 대비 교육에 대한 관심이 높습니다.",
                            "activities": {
                                "online": "주로 소셜 미디어와 뉴스 사이트를 통해 정보를 얻고, 재난 대비 관련 콘텐츠를 소비합니다."
                            },
                            "touchpoints": {
                                "online": "페이스북, 인스타그램, 유튜브 등에서 관련 콘텐츠를 소비합니다.",
                                "offline": "가정용품 매장, 재난 대비 교육 세미나 등에서 접점을 가질 수 있습니다.",
                            },
                        },
                        {
                            "segment": "20대 초중반 대학생",
                            "reason": "이 세그먼트는 자연재해에 대한 인식이 낮지만, 사회적 이슈에 민감하여 관련 제품에 관심을 가질 가능성이 높습니다.",
                            "value_prop": "환경 문제, 사회적 책임, 안전에 대한 관심이 있습니다.",
                            "activities": {"online": "주로 인스타그램과 유튜브를 통해 정보를 얻고, 관련 콘텐츠를 소비합니다."},
                            "touchpoints": {
                                "online": "인스타그램, 유튜브, 대학 커뮤니티 등에서 접점을 가질 수 있습니다.",
                                "offline": "대학 캠퍼스, 커뮤니티 센터 등에서 접점을 가질 수 있습니다.",
                            },
                        },
                        {
                            "segment": "40-50대 소상공인",
                            "reason": "이 세그먼트는 사업체 보호와 직원 안전을 중시하여 자연재해 대비 제품에 대한 수요가 높습니다.",
                            "value_prop": "사업 안전, 직원 보호, 재난 대비 교육에 대한 관심이 높습니다.",
                            "activities": {"online": "주로 비즈니스 관련 포럼과 소셜 미디어를 통해 정보를 얻고, 관련 콘텐츠를 소비합니다."},
                            "touchpoints": {
                                "online": "링크드인, 비즈니스 포럼, 관련 웹사이트 등에서 접점을 가질 수 있습니다.",
                                "offline": "비즈니스 세미나, 지역 상공회의소 등에서 접점을 가질 수 있습니다.",
                            },
                        },
                    ],
                    "limitations": [
                        {
                            "category": "법률/규제",
                            "detail": "매점매석 금지법 및 의료기기 관련 규제",
                            "impact": "법적 문제 발생 가능성",
                            "mitigation": "정부 정책 변화에 민감하게 대응",
                        },
                        {
                            "category": "특허/지적재산권",
                            "detail": "유사 특허 존재 여부 확인 필요",
                            "impact": "특허 침해 위험",
                            "mitigation": "전문가 상담을 통한 선행특허 조사",
                        },
                        {
                            "category": "시장 진입장벽",
                            "detail": "기존 경쟁사 존재 및 초기 투자 요구",
                            "impact": "시장 진입 어려움",
                            "mitigation": "차별화된 제품 개발 및 마케팅 전략 필요",
                        },
                        {
                            "category": "기술적 제약",
                            "detail": "제품 구현 난이도 및 기술 표준 충족 필요",
                            "impact": "개발 기간 지연 가능성",
                            "mitigation": "기술 개발 및 품질 관리 강화",
                        },
                    ],
                    "marketing_plan": {
                        "approach": "각 타겟 고객층에 맞춘 맞춤형 마케팅 전략을 통해 브랜드 인지도를 높이고, 고객의 신뢰를 구축합니다.",
                        "channels": ["소셜 미디어(활용도: 40%)", "온라인 광고(활용도: 30%)", "오프라인 이벤트(활용도: 30%)"],
                        "messages": [
                            "안전한 미래를 위한 준비!",
                            "자연재해 대비, 당신의 안전을 지킵니다.",
                            "필수 아이템으로 안전을 확보하세요.",
                        ],
                        "budget": 403030,
                        "kpis": ["웹사이트 방문자 수", "소셜 미디어 팔로워 수", "판매량 증가율"],
                        "phase": {
                            "pre": "소셜 미디어를 통한 티저 캠페인 및 관심 유도.",
                            "launch": "출시 이벤트 개최 및 초기 고객 피드백 수집.",
                            "growth": "고객 추천 프로그램 및 지속적인 콘텐츠 마케팅 강화.",
                        },
                    },
                    "business_model": {
                        "summary": "안전한 미래를 위한 준비, 자연재해 대비 물품!",
                        "value_proposition": {
                            "main": "고객의 안전과 자산 보호를 위한 필수 아이템을 제공합니다.",
                            "detail": "자연재해 발생 시 고객의 안전을 보장하고, 필요한 물품을 신속하게 제공하여 고객의 불안감을 해소합니다.",
                        },
                        "revenue_stream": "주요 수익원은 제품 판매로, 가격은 평균 $50-$200 사이로 설정할 예정입니다. 구독형 모델도 도입하여 정기적인 안전 점검 및 물품 보급 서비스를 제공할 계획입니다.",
                        "priorities": [
                            {
                                "name": "제품 개발(비중: 30%)",
                                "description": "고품질의 안전 제품 개발을 위해 초기 투자 필요. 고객의 요구를 반영한 제품 설계 및 테스트가 중요합니다.",
                            },
                            {
                                "name": "마케팅(비중: 25%)",
                                "description": "브랜드 인지도 향상을 위한 마케팅 캠페인에 투자. 온라인 및 오프라인 채널을 통해 고객과의 접점을 늘려야 합니다.",
                            },
                            {
                                "name": "물류 및 유통(비중: 20%)",
                                "description": "효율적인 물류 시스템 구축을 위한 투자. 고객에게 신속하게 제품을 제공하기 위한 유통망 확장이 필요합니다.",
                            },
                            {
                                "name": "고객 서비스(비중: 15%)",
                                "description": "고객 만족도를 높이기 위한 서비스 개선에 투자. 고객 피드백을 반영하여 지속적으로 서비스 품질을 향상시켜야 합니다.",
                            },
                            {
                                "name": "기술 개발(비중: 10%)",
                                "description": "IoT 및 AI 기술을 활용한 스마트 제품 개발에 투자. 고객의 안전을 더욱 강화할 수 있는 기술적 혁신이 필요합니다.",
                            },
                        ],
                        "break_even_point": "초기 투자 규모는 약 $500,000로 예상되며, 2년 내 손익분기점 도달을 목표로 합니다.",
                    },
                    "opportunities": [
                        "기후 변화에 따른 자연재해 증가로 인한 수요 증가 (근거: 기후 변화 연구 보고서)",
                        "정부의 재난 대비 정책 강화로 인한 지원 확대 (근거: 정부 정책 보고서)",
                        "재난 대비 시스템 시장의 고성장 전망 (근거: 시장 조사 보고서)",
                        "소비자 안전 의식 증가로 인한 제품 수요 증가 (근거: 소비자 조사 보고서)",
                        "기술 발전에 따른 혁신적 제품 개발 가능성 (근거: 기술 연구 보고서)",
                    ],
                    "team_requirements": [
                        {
                            "priority": "1",
                            "position": "운영 및 물류 담당자",
                            "skill": "물류 관리 및 재고 관리 경험, 협상 능력",
                            "tasks": "물품의 출처 모니터링 및 비축 관리",
                        },
                        {
                            "priority": "2",
                            "position": "마케팅 및 영업 담당자",
                            "skill": "마케팅 전략 수립 및 고객 관계 관리 경험",
                            "tasks": "제품의 브랜드 이미지 형성 및 판매 목표 달성",
                        },
                        {
                            "priority": "3",
                            "position": "제품 개발 및 연구 담당자",
                            "skill": "제품 개발 및 품질 관리 경험",
                            "tasks": "제품의 안전성 및 효율성 향상 연구",
                        },
                        {"priority": "4", "position": "재무 담당자", "skill": "재무 관리 및 회계 경험", "tasks": "예산 관리 및 재무 보고"},
                        {
                            "priority": "5",
                            "position": "고객 서비스 담당자",
                            "skill": "고객 서비스 및 문제 해결 능력",
                            "tasks": "고객 피드백 수집 및 서비스 개선",
                        },
                    ],
                },
            ]
        }
    )


class RetrieveOverviewAnalysisUsecase:
    def __init__(
        self,
        project_repository: ProjectRepository,
        overview_analysis_repository: OverviewAnalysisRepository,
        market_research_repository: MarketResearchRepository,
        market_trend_repository: MarketTrendRepository,
        revenue_benchmark_repository: RevenueBenchmarkRepository,
    ) -> None:
        self._project_repository = project_repository
        self._overview_analysis_repository = overview_analysis_repository
        self._market_research_repository = market_research_repository
        self._market_trend_repository = market_trend_repository
        self._revenue_benchmark_repository = revenue_benchmark_repository

    async def execute(
        self,
        dto: RetrieveOverviewAnalysisUsecaseDTO,
        payload: Payload,
    ) -> RetrieveOverviewAnalysisUsecaseResponse:
        try:
            overview_analysis_data = await self._overview_analysis_repository.find_by_project_id(dto.project_id)
            if not overview_analysis_data:
                raise NotFoundException("개요 분석 데이터를 찾을 수 없습니다.")

            (project, _, overview_analysis) = overview_analysis_data
            if project.user_id != payload.id:
                raise ForbiddenException("해당 프로젝트에 대한 권한이 없습니다.")

            market_research = await self._market_research_repository.find_by_ksic_hierarchy(ksic_hierarchy=overview_analysis.ksic_hierarchy)
            if market_research is None:
                raise NotFoundException("시장 조사 데이터를 찾을 수 없습니다.")
            assert market_research.id is not None

            market_trends_data = await self._market_trend_repository.find_by_market_id(market_research.id)
            if not market_trends_data:
                raise NotFoundException("시장 트렌드 데이터를 찾을 수 없습니다.")
            (domestic_market_trends, global_market_trends) = market_trends_data

            revenue_benchmarks_data = await self._revenue_benchmark_repository.find_by_market_id(market_research.id)
            if not revenue_benchmarks_data:
                raise NotFoundException("수익 벤치마크 데이터를 찾을 수 없습니다.")
            (domestic_revenue, global_revenue) = revenue_benchmarks_data

            return RetrieveOverviewAnalysisUsecaseResponse(
                score=_Score(
                    market=market_research.market_score,
                    simliar_service=overview_analysis.similarity_score,
                    risk=overview_analysis.risk_score,
                    opportunity=overview_analysis.opportunity_score,
                ),
                ksic_hierarchy=overview_analysis.ksic_hierarchy,
                evaluation=overview_analysis.evaluation,
                similar_services=overview_analysis.similar_services,
                market_trends=_MarketTrends(
                    **{
                        "domestic": [
                            _MarketTrend(
                                year=trend.year,
                                size=trend.size,
                                growth_rate=trend.growth_rate,
                                currency=trend.currency,
                                source=trend.source,
                            )
                            for trend in domestic_market_trends
                        ],
                        "global": [
                            _MarketTrend(
                                year=trend.year,
                                size=trend.size,
                                growth_rate=trend.growth_rate,
                                currency=trend.currency,
                                source=trend.source,
                            )
                            for trend in global_market_trends
                        ],
                    }
                ),
                revenue_becnhmarks=_RevenueBenchmarks(
                    **{
                        "domestic": _RevenueBenchmark(
                            average_revenue=domestic_revenue.average_revenue,
                            currency=domestic_revenue.currency,
                            source=domestic_revenue.source,
                        ),
                        "global": _RevenueBenchmark(  # type: ignore
                            average_revenue=global_revenue.average_revenue,
                            currency=global_revenue.currency,
                            source=global_revenue.source,
                        ),
                    }
                ),
                support_programs=overview_analysis.support_programs,
                target_markets=overview_analysis.target_markets,
                limitations=overview_analysis.limitations,
                marketing_plan=overview_analysis.marketing_plans,
                business_model=overview_analysis.business_model,
                opportunities=overview_analysis.opportunities,
                team_requirements=overview_analysis.team_requirements,
            )

        except RepositoryError as exception:
            raise InternalServerException(str(exception)) from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            logger.error(f"예상치 못한 오류가 발생했습니다: {str(exception)}")
            raise InternalServerException(f"예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
