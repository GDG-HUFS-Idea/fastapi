from typing import List, Dict, Any
from pydantic import ValidationError

from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient

from app.service.analyzer.dto.second_stage import (
    KeyPartnershipsInput, KeyPartnershipsOutput, PartnershipItem
)



class KeyPartnershipsAnalyzer(BlockAnalyzer[KeyPartnershipsOutput]):
    block_name = "key_partnerships"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        return []

    async def analyze(self, data: Dict[str, Any]) -> KeyPartnershipsOutput:
        inp = KeyPartnershipsInput(**data)

        user_ctx = f"""
        협업 예정: {inp.planned_collaborations or "없음"}
        진행 중 협업: {inp.ongoing_collaborations or "없음"}
        """

        schema_hint = """
        {
          "partnerships": [
            {
              "partner_type": "string",
              "purpose": "string",
              "business_link": "string or null"
            }
          ],
          "overall_structure": "string or null"
        }
        """

        prompt = make_prompt(
            role_desc="파트너십 전략 컨설턴트",
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
            return KeyPartnershipsOutput.parse_raw(raw)
        except ValidationError as e:
            raise e
