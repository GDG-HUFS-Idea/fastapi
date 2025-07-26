from typing import List, Dict, Any
from pydantic import ValidationError

from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient

from app.service.analyzer.dto.second_stage import (
    KeyResourcesInput, KeyResourcesOutput, ResourceItem
)



class KeyResourcesAnalyzer(BlockAnalyzer[KeyResourcesOutput]):
    block_name = "key_resources"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        return []

    async def analyze(self, data: Dict[str, Any]) -> KeyResourcesOutput:
        inp = KeyResourcesInput(**data)

        user_ctx = f"""
        보유 자원: {inp.owned_resources or "없음"}
        예정 자원: {inp.planned_resources or "없음"}
        부족/외부 의존: {inp.lacking_or_outsourced or "없음"}
        """

        schema_hint = """
        {
          "essential_resources": [
            {
              "category": "string",
              "name": "string",
              "link_to_value_or_relationship": "string or null"
            }
          ],
          "short_mid_long_strategy": "string or null"
        }
        """

        prompt = make_prompt(
            role_desc="비즈니스 핵심 자원 분석가",
            user_context=user_ctx,
            output_schema_hint=schema_hint
        )

        client = OpenAIClient()
        raw = await client.fetch(
            user_prompt=prompt,
            system_prompt="You are a strict JSON generator.",
            timeout_seconds=60,
            temperature=0.3,
            max_tokens=1000
        )

        try:
            return KeyResourcesOutput.parse_raw(raw)
        except ValidationError as e:
            raise e