# app/service/analyzer/blocks9_overview.py

from typing import Dict, Any, List, Tuple
from pydantic import ValidationError

from app.service.analyzer.dto.second_stage import (
    Blocks9Input, Blocks9Output, Blocks9CheckResponse, MissingField
)
from app.service.analyzer.module.second_stage.customer_segment import CustomerSegmentAnalyzer
from app.service.analyzer.module.second_stage.value_proposition import ValuePropositionAnalyzer
from app.service.analyzer.module.second_stage.channels import ChannelsAnalyzer
from app.service.analyzer.module.second_stage.customer_relationship import CustomerRelationshipAnalyzer
from app.service.analyzer.module.second_stage.revenue_streams import RevenueStreamsAnalyzer
from app.service.analyzer.module.second_stage.key_resources import KeyResourcesAnalyzer
from app.service.analyzer.module.second_stage.key_activities import KeyActivitiesAnalyzer
from app.service.analyzer.module.second_stage.key_partnerships import KeyPartnershipsAnalyzer
from app.service.analyzer.module.second_stage.cost_structure import CostStructureAnalyzer

BLOCK_ANALYZERS = {
    "customer_segment": CustomerSegmentAnalyzer(),
    "value_proposition": ValuePropositionAnalyzer(),
    "channels": ChannelsAnalyzer(),
    "customer_relationships": CustomerRelationshipAnalyzer(),
    "revenue_streams": RevenueStreamsAnalyzer(),
    "key_resources": KeyResourcesAnalyzer(),
    "key_activities": KeyActivitiesAnalyzer(),
    "key_partnerships": KeyPartnershipsAnalyzer(),
    "cost_structure": CostStructureAnalyzer(),
}


def _collect_missing(data: Dict[str, Any]) -> List[MissingField]:
    missing_list: List[MissingField] = []
    for block, analyzer in BLOCK_ANALYZERS.items():
        required = analyzer.required_fields(data.get(block) or {})
        if required:
            missing_list.append(MissingField(block=block, fields=required))
    return missing_list


async def run(data: Dict[str, Any]) -> Tuple[Blocks9CheckResponse, Blocks9Output]:
    """
    1) Blocks9Input 형식 검증
    2) 필수 입력 부족 시 Missing 반환
    3) Optional 블록에 값 없으면 AI 호출 생략(None 반환)
    4) 나머지 블록만 analyze() 실행
    """
    # 1) Pydantic 1차 검증
    try:
        Blocks9Input(**data)
    except ValidationError as e:
        # 구조 자체가 잘못된 경우엔 에러 터뜨리기
        raise e

    # 2) 필수값 체크
    missing = _collect_missing(data)
    if missing:
        return Blocks9CheckResponse(ready=False, missing=missing), Blocks9Output()

    # 3) 분석 실행
    results: Dict[str, Any] = {}
    for block, analyzer in BLOCK_ANALYZERS.items():
        block_data = data.get(block) or {}
        # Optional 블록이고, 모든 값이 None 또는 빈 리스트/문자열일 때는 건너뜀
        # (즉, 명시적 입력이 없는 경우)
        if not any(block_data.values()):
            results[block] = None
            continue

        # 그 외에만 실제 분석 호출
        results[block] = await analyzer.analyze(block_data)

    return Blocks9CheckResponse(ready=True, missing=[]), Blocks9Output(**results)
