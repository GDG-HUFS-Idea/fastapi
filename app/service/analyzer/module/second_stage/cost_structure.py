from typing import List, Dict, Any
from pydantic import ValidationError

from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient

from app.service.analyzer.dto.second_stage import (
    CostStructureInput, CostStructureOutput, CostItem
)



class CostStructureAnalyzer(BlockAnalyzer[CostStructureOutput]):
    block_name = "cost_structure"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        return []

    async def analyze(self, data: Dict[str, Any]) -> CostStructureOutput:
        inp = CostStructureInput(**data)

        user_ctx = f"""
        자금 조달 계획: {inp.funding_plan or "없음"}
        사용된 자금: {inp.spent_budget or "없음"}
        """

        schema_hint = """
        {
          "cost_items": [
            {
              "name": "string",
              "cost_type": "fixed_cost | variable_cost",
              "scale": "string or null"
            }
          ],
          "notes": "string or null"
        }
        """

        prompt = make_prompt(
            role_desc="비용 구조 분석가",
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
            return CostStructureOutput.parse_raw(raw)
        except ValidationError as e:
            raise e