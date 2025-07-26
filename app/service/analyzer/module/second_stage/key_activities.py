from typing import List, Dict, Any
from pydantic import ValidationError

from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient

from app.service.analyzer.dto.second_stage import (
    KeyActivitiesInput, KeyActivitiesOutput, ActivityItem
)



class KeyActivitiesAnalyzer(BlockAnalyzer[KeyActivitiesOutput]):
    block_name = "key_activities"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        return []

    async def analyze(self, data: Dict[str, Any]) -> KeyActivitiesOutput:
        inp = KeyActivitiesInput(**data)

        user_ctx = f"""
        가치제안 위한 핵심 업무: {inp.limited_tasks_for_value or "없음"}
        고객 접점 수단: {inp.meeting_customer_channels or "없음"}
        """

        schema_hint = """
        {
          "essential_activities": [
            {
              "name": "string",
              "order": 0,
              "criticality": "string or null"
            }
          ],
          "relationship_activities": "string or null"
        }
        """

        prompt = make_prompt(
            role_desc="핵심 활동 정의 컨설턴트",
            user_context=user_ctx,
            output_schema_hint=schema_hint
        )

        client = OpenAIClient()
        raw = await client.fetch(
            user_prompt=prompt,
            system_prompt="You are a strict JSON generator.",
            timeout_seconds=60,
            temperature=0.3,
            max_tokens=900
        )

        try:
            return KeyActivitiesOutput.parse_raw(raw)
        except ValidationError as e:
            raise e