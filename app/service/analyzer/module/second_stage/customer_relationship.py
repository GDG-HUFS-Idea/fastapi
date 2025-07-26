from typing import List, Dict, Any
from pydantic import ValidationError

from app.service.analyzer.module.second_stage.base import BlockAnalyzer, InsufficientInputError
from app.service.analyzer.module.second_stage.common_prompt import make_prompt
from app.external.openai import OpenAIClient

from app.service.analyzer.dto.second_stage import (
    CustomerRelationshipsInput, CustomerRelationshipsOutput, RelationshipItem
)



class CustomerRelationshipAnalyzer(BlockAnalyzer[CustomerRelationshipsOutput]):
    block_name = "customer_relationships"

    @staticmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        return []

    async def analyze(self, data: Dict[str, Any]) -> CustomerRelationshipsOutput:
        inp = CustomerRelationshipsInput(**data)

        user_ctx = f"""
        소통 방식: {inp.communication_methods or "없음"}
        리텐션 방법: {inp.retention_methods or "없음"}
        최근 불만 & 대응: {inp.recent_complaints or "없음"}
        고객 정보 정리 방식: {inp.customer_info_management or "없음"}
        """

        schema_hint = """
        {
          "relationship_strategies": [
            {
              "relationship_type": "personal_assistance | self_service | automated_service | community | co_creation",
              "description": "string"
            }
          ],
          "loyalty_strategy": "string or null"
        }
        """

        prompt = make_prompt(
            role_desc="고객 관계 관리(CRM) 전략가",
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
            return CustomerRelationshipsOutput.parse_raw(raw)
        except ValidationError as e:
            raise e