import asyncio
from datetime import timedelta
import logging
import re
from typing import List, Optional, Union, cast
from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

from app.common import schemas
from app.common.enums import Currency, MarketScope, ProjectStatus, TaskStatus
from app.core.cache import get_static_redis_session
from app.core.database import get_static_db_session
from app.domain.market_research import MarketResearch
from app.domain.market_trend import MarketTrend
from app.domain.overview_analysis import OverviewAnalysis
from app.domain.project import Project
from app.repository.project_idea import ProjectIdea
from app.domain.revenue_benchmark import RevenueBenchmark
from app.repository.market_research import MarketResearchRepository
from app.repository.market_trend import MarketTrendRepository
from app.repository.overview_analysis import OverviewAnalysisRepository
from app.repository.project import ProjectRepository
from app.repository.project_idea import ProjectIdeaRepository
from app.repository.revenue_benchmark import RevenueBenchmarkRepository
from app.service.analyzer.overview_analysis import (
    _MarketSizeData,
    _MarketSizeSource,
    OverviewAnalysisService,
    OverviewAnalysisServiceResponse,
)
from app.service.analyzer.pre_analysis_data import PreAnalysisDataService
from app.service.auth.jwt import Payload
from app.service.cache.task_progress import TaskProgress, TaskProgressCache
from app.common.exceptions import (
    UsecaseException,
    UnauthorizedException,
    InternalServerException,
    CacheError,
)

logger = logging.getLogger(__name__)


class StartOverviewAnalysisTaskUsecaseDTO(BaseModel):
    problem: str = Field(description="해결하고자 하는 문제에 대한 설명", min_length=1)
    solution: str = Field(description="제안하는 솔루션에 대한 설명", min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "problem": "자연재해가 빈번하게 발생하는 상황에서 시민들이 필요한 비상용품을 빠르게 구매하기 어려운 문제가 있습니다.",
                    "solution": "재해 대비 용품을 전문적으로 판매하는 온라인 플랫폼을 구축하여 시민들이 필요한 물품을 쉽게 구매할 수 있도록 하겠습니다.",
                }
            ]
        }
    )


class StartOverviewAnalysisTaskUsecaseResponse(BaseModel):
    task_id: str = Field(description="생성된 작업 ID (진행 상태 조회에 사용)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_id": "uNkpUsM54EZ49CnUjRp_OA",
                }
            ]
        }
    )


class StartOverviewAnalysisTaskUsecase:
    _TASK_EXPIRE_DELTA = timedelta(seconds=600)

    def __init__(
        self,
        pre_analysis_data_service: PreAnalysisDataService,
        overview_analysis_service: OverviewAnalysisService,
        task_progress_cache: TaskProgressCache,
    ) -> None:
        self._pre_analysis_data_service = pre_analysis_data_service
        self._overview_analysis_stream_service = overview_analysis_service
        self._task_progress_cache = task_progress_cache

    async def execute(
        self,
        request: Request,
        dto: StartOverviewAnalysisTaskUsecaseDTO,
        payload: Payload,
    ) -> StartOverviewAnalysisTaskUsecaseResponse:
        try:
            # 1. 클라이언트 호스트 정보 조회 및 작업 시작 시간 기록
            start_time = asyncio.get_event_loop().time()
            host: Optional[str] = getattr(request.client, "host", None)
            if not host:
                raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

            # 2. 작업 진행 상태 캐시에 저장
            task_id = await self._task_progress_cache.set(
                data=TaskProgress(
                    status=TaskStatus.IN_PROGRESS,
                    progress=0.0,
                    message="분석을 시작합니다.",
                    host=host,
                    user_id=payload.id,
                    start_time=start_time,
                ),
                expire_delta=self._TASK_EXPIRE_DELTA,
            )

            # 3. 백그라운드에서 분석 파이프라인 실행
            asyncio.create_task(self._run_analysis_pipeline(task_id, dto.problem, dto.solution, payload))

            # 4. 즉시 작업 ID 반환
            return StartOverviewAnalysisTaskUsecaseResponse(task_id=task_id)

        except CacheError as exception:
            raise InternalServerException(str(exception)) from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            raise InternalServerException(f"분석 작업 시작 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def _run_analysis_pipeline(
        self,
        task_id: str,
        problem: str,
        solution: str,
        payload: Payload,
    ) -> None:
        try:
            redis_session = await get_static_redis_session()
            self._task_progress_cache = TaskProgressCache(session=redis_session)

            async with get_static_db_session() as session:
                project_repository = ProjectRepository(session=session)
                project_idea_repository = ProjectIdeaRepository(session=session)
                market_research_repository = MarketResearchRepository(session=session)
                market_trend_repository = MarketTrendRepository(session=session)
                revenue_benchmark_repository = RevenueBenchmarkRepository(session=session)
                overview_analysis_repository = OverviewAnalysisRepository(session=session)

                # 1. 프로젝트 초기화 및 저장
                project = Project(
                    user_id=payload.id,
                    name="미정",
                    status=ProjectStatus.IN_PROGRESS,
                )
                await project_repository.save(project)
                await session.commit()

                # 2. 사전 분석 실행
                pre_analysis_data = await self._pre_analysis_data_service.analyze(task_id, problem, solution)

                project.name = pre_analysis_data.idea
                await project_repository.save(project)
                await session.commit()

                # 3. 본 분석 실행
                raw_overview_analysis = await self._overview_analysis_stream_service.analyze(task_id, pre_analysis_data)

                # 4. 프로젝트 최종 저장
                project.status = ProjectStatus.ANALYZED
                await project_repository.save(project)

                # 5. 아이디어 저장
                project_idea = ProjectIdea(
                    project_id=cast(int, project.id),
                    problem=problem,
                    solution=solution,
                    issues=pre_analysis_data.business_case.problem.issues,
                    motivation=pre_analysis_data.business_case.problem.motivation,
                    features=pre_analysis_data.business_case.solution.features,
                    method=pre_analysis_data.business_case.solution.method,
                    deliverable=pre_analysis_data.business_case.solution.deliverable,
                )
                await project_idea_repository.save(project_idea)

                ksic_hierarchy = schemas.KSICHierarchy(
                    large=schemas.KSICItem(
                        code=raw_overview_analysis.ksic_hierarchy.large.code,
                        name=raw_overview_analysis.ksic_hierarchy.large.name,
                    ),
                    medium=schemas.KSICItem(
                        code=raw_overview_analysis.ksic_hierarchy.medium.code,
                        name=raw_overview_analysis.ksic_hierarchy.medium.name,
                    ),
                    small=schemas.KSICItem(
                        code=raw_overview_analysis.ksic_hierarchy.small.code,
                        name=raw_overview_analysis.ksic_hierarchy.small.name,
                    ),
                    detail=schemas.KSICItem(
                        code=raw_overview_analysis.ksic_hierarchy.detail.code,
                        name=raw_overview_analysis.ksic_hierarchy.detail.name,
                    ),
                )

                # 6. 시장 조사 데이터 저장
                market_research = MarketResearch(
                    ksic_hierarchy=ksic_hierarchy.model_dump(),  # type: ignore
                    market_score=raw_overview_analysis.scores.market,
                )
                await market_research_repository.save(market_research)
                assert market_research.id is not None

                # 7. 시장 트렌드 데이터 처리
                domestic_market_trends, global_market_trends = self._create_market_trends(raw_overview_analysis, market_research.id)
                await market_trend_repository.save_batch(domestic_market_trends + global_market_trends)

                # 8. 수익 벤치마크 데이터 처리
                domestic_revenue_benchmark, global_revenue_benchmark = self._create_revenue_benchmarks(
                    raw_overview_analysis, market_research.id
                )
                await revenue_benchmark_repository.save_batch([domestic_revenue_benchmark, global_revenue_benchmark])

                # 9. 개요 분석 결과 저장
                overview_analysis = self._create_overview_analysis(raw_overview_analysis, ksic_hierarchy, project_idea)
                await overview_analysis_repository.save(overview_analysis)

            # 10. 분석 완료 상태 저장
            await self._task_progress_cache.update_partial(
                key=task_id,
                status=TaskStatus.COMPLETED,
                progress=1.0,
                project_id=project.id,
                message="분석이 완료되었습니다.",
            )

        except Exception as exception:
            await self._task_progress_cache.update_partial(
                key=task_id,
                status=TaskStatus.FAILED,
                message="분석 중 오류가 발생했습니다.",
            )
            logger.error(f"분석 파이프라인에서 오류 발생: {str(exception)}")
            raise

    def _create_revenue_benchmarks(
        self,
        raw_overview_analysis: OverviewAnalysisServiceResponse,
        market_research_id: int,
    ) -> tuple[RevenueBenchmark, RevenueBenchmark]:
        domestic_revenue_benchmark = RevenueBenchmark(
            market_id=market_research_id,
            scope=MarketScope.DOMESTIC,
            average_revenue=int(raw_overview_analysis.average_revenue.domestic.replace('$', '').replace(',', '')),
            currency=Currency.USD,
            source=raw_overview_analysis.average_revenue.source,
        )

        # 글로벌 평균 수익
        global_revenue_benchmark = RevenueBenchmark(
            market_id=market_research_id,
            scope=MarketScope.GLOBAL,
            average_revenue=int(raw_overview_analysis.average_revenue.global_.replace('$', '').replace(',', '')),
            currency=Currency.USD,
            source=raw_overview_analysis.average_revenue.source,
        )

        return domestic_revenue_benchmark, global_revenue_benchmark

    def _create_market_trends(
        self,
        raw_overview_analysis: OverviewAnalysisServiceResponse,
        market_research_id: int,
    ) -> tuple[List[MarketTrend], List[MarketTrend]]:
        domestic_market_trends = []
        global_market_trends = []

        # 국내
        domestic_source = None
        for item in raw_overview_analysis.market_size_by_year.domestic:
            if isinstance(item, _MarketSizeData):
                market_trend = MarketTrend(
                    market_id=market_research_id,
                    scope=MarketScope.DOMESTIC,
                    year=item.year,
                    size=int(item.size.replace('$', '').replace(',', '')),
                    currency=Currency.KRW,  # 기본 원화
                    growth_rate=float(item.growth_rate.replace('%', '')),
                    source="",  # 임시
                )
                domestic_market_trends.append(market_trend)
            elif isinstance(item, _MarketSizeSource):
                domestic_source = item.source

        # 글로벌
        global_source = None
        for item in raw_overview_analysis.market_size_by_year.global_:
            if isinstance(item, _MarketSizeData):
                market_trend = MarketTrend(
                    market_id=market_research_id,
                    scope=MarketScope.GLOBAL,
                    year=item.year,
                    size=int(item.size.replace('$', '').replace(',', '')),
                    currency=Currency.USD,  # 기본 달러
                    growth_rate=float(item.growth_rate.replace('%', '')),
                    source="",  # 임시
                )
                global_market_trends.append(market_trend)
            elif isinstance(item, _MarketSizeSource):
                global_source = item.source

        for trend in domestic_market_trends:
            trend.source = domestic_source
        for trend in global_market_trends:
            trend.source = global_source
        return domestic_market_trends, global_market_trends

    def _parse_budget(
        self,
        budget_str: Union[str, int, None] = None,
    ) -> int:
        if isinstance(budget_str, int):
            return budget_str
        if isinstance(budget_str, str):
            # 숫자만 추출
            numbers = re.findall(r'\d+', budget_str.replace(',', ''))
            return int(''.join(numbers)) if numbers else 0
        return 0

    def _create_overview_analysis(
        self,
        raw_overview_analysis: OverviewAnalysisServiceResponse,
        ksic_hierarchy: schemas.KSICHierarchy,
        project_idea: ProjectIdea,
    ) -> OverviewAnalysis:
        assert project_idea.id is not None

        return OverviewAnalysis(
            idea_id=project_idea.id,
            evaluation=raw_overview_analysis.one_line_review,
            ksic_hierarchy=ksic_hierarchy.model_dump(),  # type: ignore
            similarity_score=raw_overview_analysis.scores.similar_service,
            risk_score=raw_overview_analysis.scores.risk,
            opportunity_score=raw_overview_analysis.scores.opportunity,
            similar_services=[
                schemas.SimilarService(
                    name=service.name,
                    description=service.description,
                    logo_url="",  # TODO: 로고 URL 처리
                    website=service.url,
                    tags=service.tags,
                    summary=service.summary,
                ).model_dump()
                for service in raw_overview_analysis.similar_services
            ],  # type: ignore
            support_programs=[
                schemas.SupportProgram(
                    name=program.name,
                    organizer=program.organization,
                    url="",  # TODO: URL 처리
                    start_date=program.period,  # TODO: 날짜 처리
                    end_date=program.period,  # TODO: 날짜 처리
                ).model_dump()
                for program in raw_overview_analysis.support_programs
            ],  # type: ignore
            target_markets=[
                schemas.TargetMarket(
                    segment=target.segment,
                    reason=target.reasons,
                    value_prop=target.interest_factors,
                    activities=schemas.TargetMarketActivity(
                        online=target.online_activities,
                    ),
                    touchpoints=schemas.TargetMarketTouchpoint(
                        online=target.online_touchpoints,
                        offline=target.offline_touchpoints,
                    ),
                ).model_dump()
                for target in raw_overview_analysis.target_audience
            ],  # type: ignore
            marketing_plans=schemas.MarketingPlan(
                approach=raw_overview_analysis.marketing_strategy.approach,
                channels=raw_overview_analysis.marketing_strategy.channels,
                messages=raw_overview_analysis.marketing_strategy.messages,
                budget=self._parse_budget(raw_overview_analysis.marketing_strategy.budget_allocation),
                kpis=raw_overview_analysis.marketing_strategy.kpis,
                phase=schemas.MarketingPlanPhase(
                    pre=raw_overview_analysis.marketing_strategy.phased_strategy.pre_launch,
                    launch=raw_overview_analysis.marketing_strategy.phased_strategy.launch,
                    growth=raw_overview_analysis.marketing_strategy.phased_strategy.growth,
                ),
            ).model_dump(),  # type: ignore
            business_model=schemas.BusinessModel(
                summary=raw_overview_analysis.business_model.tagline,
                value_proposition=schemas.BusinessModelValueProposition(
                    main=raw_overview_analysis.business_model.value,
                    detail=raw_overview_analysis.business_model.value_details,
                ),
                revenue_stream=raw_overview_analysis.business_model.revenue_structure,
                priorities=[
                    schemas.BusinessModelPriority(
                        name=priority.name,
                        description=priority.description,
                    )
                    for priority in raw_overview_analysis.business_model.investment_priorities
                ],
                break_even_point=raw_overview_analysis.business_model.break_even_point,
            ).model_dump(),  # type: ignore
            opportunities=raw_overview_analysis.opportunities,
            limitations=[
                schemas.Limitation(
                    category=risk.category,
                    detail=risk.details,
                    impact=risk.impact,
                    mitigation=risk.solution,
                ).model_dump()
                for risk in raw_overview_analysis.limitations
            ],  # type: ignore
            team_requirements=[
                schemas.TeamRequirement(
                    priority=requirement.priority if isinstance(requirement.priority, str) else str(requirement.priority),
                    position=requirement.title,
                    skill=requirement.skills,
                    tasks=requirement.responsibilities,
                ).model_dump()
                for requirement in raw_overview_analysis.required_team.roles
            ],  # type: ignore
        )
