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
                progress=round(random.uniform(0.06, 0.12), 2),
                message="아이디어 요약 중입니다...",
            )
            idea = await self._idea_summation_service.execute(problem, solution)

            # 3. 사전 분석 데이터 준비
            logger.info(f"사전 분석 데이터 준비 중")
            await self._task_progress_cache.update_partial(
                key=task_id,
                progress=round(random.uniform(0.12, 0.17), 2),
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

# helper: 딕셔너리 경로 탐색
from typing import Any, Dict

def _dig(obj: Dict[str, Any], path: str, default=None):
    parts = path.split(".")
    cur = obj
    for p in parts:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur

# helper: 문자열 정규화
def _normalize_str(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None

# 2차 기능 매핑 테이블 (1차 PreAnalysis 결과 → 9Blocks Input)
# Python 속성명 기준으로, raw_input["business_case"] 등에서 꺼냅니다.
_MAPPING_TABLE: Dict[str, Dict[str, str]] = {
    "customer_segment": {
        # run_blocks9_analysis.py 의 problem_dict["developmentMotivation"]
        "service_purpose": "problem.developmentMotivation",
    },
    "value_proposition": {
        # run_blocks9_analysis.py 의 solution_dict["coreElements"]
        "unique_features":              "solution.coreElements",
        # 1차 리포트 의 businessModel.value 필드 활용
        "emotional_or_practical_value": "businessModel.value",
    },
    "channels": {
        # 1차 리포트의 마케팅 전략 채널 및 KPI
        "performance_metrics":      "marketingStrategy.kpis",
        "main_touchpoints":         "marketingStrategy.channels",
        "tried_marketing_channels": "marketingStrategy.channels",
        "sales_distribution":       "businessModel.revenueStructure",
    },
    "customer_relationships": {},    # 사용자 보완 입력 전용
    "revenue_streams": {
        # 1차 리포트의 비즈니스 모델 수익 구조 및 평균 수익 활용
        "current_revenue_model": "businessModel.revenueStructure",
        "pricing_policy":        "businessModel.revenueStructure",
        "revenue_amount":        "averageRevenue.domestic",
    },
    "key_resources": {},            # 사용자 보완 입력 전용
    "key_activities": {},           # 사용자 보완 입력 전용
    "key_partnerships": {},         # 사용자 보완 입력 전용
    "cost_structure": {},           # 사용자 보완 입력 전용
}


def to_second_stage_dict(raw_input: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    1차 분석 결과(raw_input) + 사용자 보완 입력 → 9Blocks 각 섹션 Input dict로 변환
    - _MAPPING_TABLE 기준으로 추출, 사용자 override 값이 있으면 우선 사용
    """
    result: Dict[str, Dict[str, Any]] = {}
    for block, field_map in _MAPPING_TABLE.items():
        override = raw_input.get(block) or {}
        mapped: Dict[str, Any] = {}
        for out_field, path in field_map.items():
            if out_field in override:
                mapped[out_field] = override[out_field]
            else:
                mapped[out_field] = _normalize_str(_dig(raw_input, path))
        result[block] = mapped
    return result