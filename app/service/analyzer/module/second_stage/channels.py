from typing import List, Dict, Any
from pydantic import ValidationError

from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient

from app.service.analyzer.dto.second_stage import (
    ChannelsInput, ChannelsOutput, ChannelStageItem
)


class ChannelsAnalyzer(BlockAnalyzer[ChannelsOutput]):
    block_name = "channels"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        # 선택 입력만 존재 -> 필수 없음
        return []

    async def analyze(self, data: Dict[str, Any]) -> ChannelsOutput:
        inp = ChannelsInput(**data)

        user_ctx = f"""
        성과 지표(MAU/WAU 등): {inp.performance_metrics or "없음"}
        주요 접점: {inp.main_touchpoints or "없음"}
        사용해본 마케팅 채널 & 성과: {inp.tried_marketing_channels or "없음"}
        판매/유통 방식: {inp.sales_distribution or "없음"}
        """

        schema_hint = """
        {
          "journey_channels": [
            {
              "stage": "인지|고려|구매|유지|추천",
              "channels": ["string", "..."],
              "strategy_or_roi": "string or null"
            }
          ],
          "improvement_points": "string or null",
          "convenience_vs_competition": "string or null"
        }
        """

        prompt = make_prompt(
            role_desc="마케팅 채널 전략 컨설턴트",
            user_context=user_ctx,
            output_schema_hint=schema_hint
        )

        client = OpenAIClient()
        raw = await client.fetch(
            user_prompt=prompt,
            system_prompt="You are a strict JSON generator.",
            timeout_seconds=60,
            temperature=0.3,
            max_tokens=1200
        )

        try:
            return ChannelsOutput.parse_raw(raw)
        except ValidationError as e:
            raise e