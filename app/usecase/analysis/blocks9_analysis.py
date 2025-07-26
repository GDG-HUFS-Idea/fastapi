# 유스케이스

from typing import Any, Dict
from app.service.analyzer.blocks9_overview import run as run_blocks9
from app.service.analyzer.pre_analysis_data import to_second_stage_dict
from app.common.schemas.response import SuccessResponse

class Blocks9AnalysisUsecase:
    async def execute(self, raw_input: Dict[str, Any]):
        # 1차 결과 + 사용자 추가 입력 → 2차용 dict 변환
        second_stage_data = to_second_stage_dict(raw_input)
        check, output = await run_blocks9(second_stage_data)

        return SuccessResponse(data={
            "check": check.dict(),
            "result": output.dict()
        })
