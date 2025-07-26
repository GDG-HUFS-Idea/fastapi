# fastapi/app/usecase/analysis/blocks9_analysis.py

from typing import Any, Dict
import logging

from app.service.analyzer.blocks9_overview import run as run_blocks9
from app.service.analyzer.pre_analysis_data import to_second_stage_dict

logger = logging.getLogger(__name__)


class Blocks9AnalysisUsecase:
    """
    2차 기능: 9Blocks 상세 리포트 생성 유스케이스
    """

    async def execute(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        raw_input:
          - 1차 분석 결과 + 개요 분석 결과 + (옵션) 사용자 보완 입력
        반환:
          {
            "check": { "ready": bool, "missing": [...] },
            "result": { ... 9개 블록별 Output ... }
          }
        """
        # 1) 1차 결과 및 사용자 보완 입력 → 2차 DTO 구조로 변환
        second_stage_data = to_second_stage_dict(raw_input)

        # 2) 누락값 검사 및 블록별 분석
        check, output = await run_blocks9(second_stage_data)

        # 3) 결과를 dict 형태로 반환
        return {
            "check": check.dict(),
            "result": output.dict()
        }
