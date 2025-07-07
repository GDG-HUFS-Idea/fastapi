import asyncio
import logging
import random
from pydantic import BaseModel

from app.common.enums import TaskStatus
from app.core.cache import get_static_redis_session
from app.service.analyzer.module.business_case_extraction import (
    BusinessCaseExtractionService,
    BusinessCaseExtractionServiceResponse,
)
from app.service.analyzer.module.limitation_analysis import LimitationAnalysisService
from app.service.analyzer.module.opportunity_analysis import OpportunityAnalysisService
from app.service.analyzer.module.similar_service_research import (
    SimilarServiceResearchService,
    SimilarServiceResearchServiceResponse,
)
from app.service.analyzer.module.idea_summation import IdeaSummationService
from app.service.analyzer.module.market_research import MarketResearchService, MarketResearchServiceResponse
from app.service.analyzer.module.team_requirement_analysis import TeamRequirementAnalysisService
from app.service.cache.task_progress import TaskProgressCache

logger = logging.getLogger(__name__)


class PreAnalysisDataServiceResponse(BaseModel):
    idea: str
    business_case: BusinessCaseExtractionServiceResponse
    similar_service: SimilarServiceResearchServiceResponse
    market: MarketResearchServiceResponse
    limitation: str
    opportunity: str
    team_requirement: str


class PreAnalysisDataService:
    def __init__(
        self,
    ) -> None:
        self._business_case_extraction_service = BusinessCaseExtractionService()
        self._idea_summation_service = IdeaSummationService()
        self._similar_service_research_service = SimilarServiceResearchService()
        self._market_research_service = MarketResearchService()
        self._limitation_analysis_service = LimitationAnalysisService()
        self._opportunity_analysis_service = OpportunityAnalysisService()
        self._team_requirement_analysis_servce = TeamRequirementAnalysisService()

    async def analyze(
        self,
        task_id: str,
        problem: str,
        solution: str,
    ) -> PreAnalysisDataServiceResponse:
        try:
            redis = await get_static_redis_session()
            self._task_progress_cache = TaskProgressCache(session=redis)

            # 1. 비즈니스 케이스(5개) 추출
            logger.info(f"비즈니스 케이스 추출 중")
            await self._task_progress_cache.update_partial(
                key=task_id,
                progress=round(random.uniform(0.00, 0.06), 2),
                message="비즈니스 케이스 추출 중입니다...",
            )
            business_case = await self._business_case_extraction_service.execute(problem, solution)
            issues = business_case.problem.issues
            features, method = business_case.solution.features, business_case.solution.method

            # 2. 아이디어 요약
            logger.info(f"아이디어 요약 중")
            await self._task_progress_cache.update_partial(
                key=task_id,
                progress=round(random.uniform(0.06, 0.17), 2),
                message="아이디어 요약 중입니다...",
            )
            idea = await self._idea_summation_service.execute(problem, solution)

            # 3. 사전 분석 데이터 준비
            logger.info(f"사전 분석 데이터 준비 중")
            await self._task_progress_cache.update_partial(
                key=task_id,
                progress=round(random.uniform(0.17, 0.33), 2),
                message="사전 분석 데이터 준비 중입니다...",
            )
            (similar_service, market, limitation, opportunity, team_requirement) = await asyncio.gather(
                self._similar_service_research_service.execute(idea, features),
                self._market_research_service.execute(idea, issues, features, method),
                self._limitation_analysis_service.execute(idea, issues, features),
                self._opportunity_analysis_service.execute(idea, issues, features),
                self._team_requirement_analysis_servce.execute(idea, issues, features),
            )

            return PreAnalysisDataServiceResponse(
                idea=idea,
                business_case=business_case,
                similar_service=similar_service,
                market=market,
                limitation=limitation,
                opportunity=opportunity,
                team_requirement=team_requirement,
            )
        except Exception:
            await self._task_progress_cache.update_partial(
                key=task_id,
                status=TaskStatus.FAILED,
                message=f"사전 분석 데이터 준비 중 오류가 발생했습니다. 나중에 다시 시도해 주세요.",
            )
            raise
