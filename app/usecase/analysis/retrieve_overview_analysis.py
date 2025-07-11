import logging
from typing import List
from fastapi import Query
from pydantic import BaseModel, Field

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
    project_id: int = Field(Query())


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
