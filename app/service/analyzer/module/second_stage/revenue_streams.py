from typing import List, Dict, Any
from pydantic import ValidationError

from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient

from app.service.analyzer.dto.second_stage import (
    RevenueStreamsInput, RevenueStreamsOutput, RevenueItem
)



class RevenueStreamsAnalyzer(BlockAnalyzer[RevenueStreamsOutput]):
    block_name = "revenue_streams"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        return []

    async def analyze(self, data: Dict[str, Any]) -> RevenueStreamsOutput:
        inp = RevenueStreamsInput(**data)

        user_ctx = f"""
        현재 수익 모델: {inp.current_revenue_model or "없음"}
        결제 시점: {inp.payment_timing or "없음"}
        가격 정책: {inp.pricing_policy or "없음"}
        현재 수익/금액 & 이유: {inp.revenue_amount or "없음"}
        """

        schema_hint = """
        {
          "revenue_flows": [
            {
              "revenue_type": "sales_revenue | subscription_fee | advertisement | transaction_fee | licensing | other",
              "detail": "string",
              "reason": "string or null"
            }
          ],
          "expansion_ideas": "string or null"
        }
        """

        prompt = make_prompt(
            role_desc="수익 모델 설계 전문가",
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
            return RevenueStreamsOutput.parse_raw(raw)
        except ValidationError as e:
            raise e