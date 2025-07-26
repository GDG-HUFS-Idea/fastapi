from typing import List, Dict, Any
from pydantic import ValidationError

from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient

from app.service.analyzer.dto.second_stage import (
    ValuePropositionInput, ValuePropositionOutput, CompetitorDiffItem
)



class ValuePropositionAnalyzer(BlockAnalyzer[ValuePropositionOutput]):
    block_name = "value_proposition"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        # 해당 블록은 모두 선택 입력이라 필수값 없음 (필요 시 확장)
        return []

    async def analyze(self, data: Dict[str, Any]) -> ValuePropositionOutput:
        # DTO 검증 (필수 없으므로 바로 진행 가능)
        inp = ValuePropositionInput(**data)

        user_ctx = f"""
        독특한 기능/경험: {inp.unique_features or "없음"}
        인상 깊은 피드백: {inp.memorable_feedback or "없음"}
        감정적/실용적 가치: {inp.emotional_or_practical_value or "없음"}
        """

        schema_hint = """
        {
          "core_value_one_liner": "string",
          "problem_solution_flow": "string",
          "competitor_diff": [
            {"factor": "string", "explanation": "string"}
          ],
          "emotional_benefit_summary": "string or null"
        }
        """

        prompt = make_prompt(
            role_desc="가치 제안(Value Proposition) 전문가",
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
            return ValuePropositionOutput.parse_raw(raw)
        except ValidationError as e:
            raise e
