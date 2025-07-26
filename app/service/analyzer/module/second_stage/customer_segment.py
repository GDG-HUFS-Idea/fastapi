# app/service/analyzer/module/second_stage/customer_segment.py
from typing import List, Dict, Any
from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.dto.second_stage import (
    CustomerSegmentOutput, CustomerSegmentInput, CustomerNeedItem
)
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient  # 실제 경로 확인
from pydantic import ValidationError

class CustomerSegmentAnalyzer(BlockAnalyzer[CustomerSegmentOutput]):
    block_name = "customer_segment"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        must = ["service_purpose"]  # 필수 필드 정의
        return [m for m in must if not data.get(m)]

    async def analyze(self, data: Dict[str, Any]) -> CustomerSegmentOutput:
        missing = self.required_fields(data)
        if missing:
            raise InsufficientInputError(self.block_name, missing)

        inp = CustomerSegmentInput(**data)

        user_ctx = f"""
        목적/필요성: {inp.service_purpose}
        고객 검증 활동: {inp.validation_activities or "없음"}
        사용자 특성/맥락: {inp.user_characteristics or "없음"}
        """

        schema_hint = """
        {
          "target_market": "string",
          "customer_groups": ["string", "..."],
          "market_type": "mass_market | niche_market | segmented_market | multi_sided_platform",
          "reason_for_market_type": "string",
          "common_needs_table": [
            {
              "segment": "string",
              "pain": "string or null",
              "need": "string or null",
              "opportunity": "string or null"
            }
          ]
        }
        """

        prompt = make_prompt(
            role_desc="시장/고객 세분화 전문가",
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
            return CustomerSegmentOutput.parse_raw(raw)
        except ValidationError as e:
            raise e
