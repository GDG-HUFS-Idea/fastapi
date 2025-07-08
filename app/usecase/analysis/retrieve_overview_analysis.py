import logging
from typing import List, Optional
from fastapi import Query
from pydantic import BaseModel

from app.domain.market_research import MarketResearch
from app.domain.market_trend import MarketTrend
from app.domain.overview_analysis import OverviewAnalysis
from app.domain.revenue_benchmark import RevenueBenchmark
from app.repository.market_research import MarketResearchRepository
from app.repository.market_trend import MarketTrendRepository
from app.repository.overview_analysis import OverviewAnalysisRepository
from app.repository.project import ProjectRepository
from app.repository.revenue_benchmark import RevenueBenchmarkRepository
from app.service.auth.jwt import Payload
from app.common.exceptions import NotFoundException, RepositoryError, UsecaseException, InternalServerException

logger = logging.getLogger(__name__)


class RetrieveOverviewAnalysisUsecaseDTO(BaseModel):
    project_id: int = Query()


class RetrieveOverviewAnalysisUsecaseResponse(BaseModel):
    overview_analysis: OverviewAnalysis
    market_research: Optional[MarketResearch] = None
    domestic_market_trends: List[MarketTrend] = []
    global_market_trends: List[MarketTrend] = []
    domestic_revenue_benchmark: Optional[RevenueBenchmark] = None
    global_revenue_benchmark: Optional[RevenueBenchmark] = None


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
            # 프로젝트 ID로 개요 분석 조회
            overview_analysis = await self._overview_analysis_repository.find_by_project_id(dto.project_id)
            if not overview_analysis:
                raise NotFoundException(f"프로젝트({dto.project_id})에 대한 분석 결과를 찾을 수 없습니다")

            # TODO: 소유자 확인 필요

            # KSIC 계층 구조로 시장 분석 및 관련 데이터 조회
            hierarchy_data = overview_analysis.ksic_hierarchy
            if isinstance(hierarchy_data, dict):
                ksic_hierarchy_string = ">".join(
                    [
                        hierarchy_data["large"]["name"],
                        hierarchy_data["medium"]["name"],
                        hierarchy_data["small"]["name"],
                        hierarchy_data["detail"]["name"],
                    ]
                )
            else:
                # _KSICHierarchy 객체인 경우
                ksic_hierarchy_string = ">".join(
                    [
                        hierarchy_data.large.name,
                        hierarchy_data.medium.name,
                        hierarchy_data.small.name,
                        hierarchy_data.detail.name,
                    ]
                )

            market_data = await self._market_research_repository.find_joined_by_ksic_hierarchy(ksic_hierarchy=ksic_hierarchy_string)

            # 시장 데이터가 없는 경우 기본 응답 반환
            if market_data is None:
                raise NotFoundException(f"프로젝트({dto.project_id})에 대한 시장 분석 데이터를 찾을 수 없습니다")

            # 시장 데이터 언패킹
            (
                market_research,
                domestic_trends,
                global_trends,
                domestic_revenue,
                global_revenue,
            ) = market_data

            return RetrieveOverviewAnalysisUsecaseResponse(
                overview_analysis=overview_analysis,
                market_research=market_research,
                domestic_market_trends=domestic_trends,
                global_market_trends=global_trends,
                domestic_revenue_benchmark=domestic_revenue,
                global_revenue_benchmark=global_revenue,
            )

        except RepositoryError as exception:
            raise InternalServerException(str(exception)) from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            logger.error(f"예상치 못한 오류가 발생했습니다: {str(exception)}")
            raise InternalServerException(f"예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
