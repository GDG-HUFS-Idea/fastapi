import json
import logging
from textwrap import dedent
from typing import List
from pydantic import BaseModel, Field, ValidationError

from app.common.utils import retry, validate_json
from app.external.openai import OpenAIClient
from app.common.exceptions import AnalysisServiceError, ExternalAPIError, JSONValidationError, ModelValidationError

logger = logging.getLogger(__name__)


class _Item(BaseModel):
    name: str
    url: str
    description: str
    target_audience: str = Field(alias="targetAudience")
    tags: List[str]
    summary: str
    similarity: int


class SimilarServiceResearchServiceResponse(BaseModel):
    items: List[_Item]


class SimilarServiceResearchService:
    _TIMEOUT_SECONDS = 60 * 3
    _TEMPERATURE = 0.3
    _MAX_TOKENS = 2000
    _MAX_ATTEMPTS = 3

    def __init__(self) -> None:
        self._openAI_search_client = OpenAIClient()

    async def execute(
        self,
        idea: str,
        features: List[str],
    ) -> SimilarServiceResearchServiceResponse:
        try:

            async def operation():
                content = await self._openAI_search_client.search(
                    input=self._generate_prompt(idea, features),
                    timeout_seconds=self._TIMEOUT_SECONDS,
                    temperature=self._TEMPERATURE,
                    max_output_tokens=self._MAX_TOKENS,
                )

                # 디버깅: 원본 응답 로깅
                logger.debug(f"Perplexity 원본 응답 길이: {len(content)}")
                logger.debug(f"Perplexity 원본 응답 (처음 500자): {content[:500]}")
                logger.debug(f"Perplexity 원본 응답 (마지막 500자): {content[-500:]}")

                validated_json = validate_json(content)
                parsed_data = json.loads(validated_json)

                # 응답 검증: 리스트이고 최소 1개 이상의 항목이 있는지 확인
                if not isinstance(parsed_data, list) or len(parsed_data) == 0:
                    raise JSONValidationError("응답이 유효한 배열이 아니거나 비어있습니다")

                return SimilarServiceResearchServiceResponse(items=parsed_data)

            return await retry(
                function=operation,
                max_attempts=self._MAX_ATTEMPTS,
            )

        except JSONValidationError as exception:
            raise JSONValidationError(f"유사 서비스 조사 JSON 형식 검증 오류가 발생했습니다: {str(exception)}") from exception
        except ValidationError as exception:
            raise ModelValidationError(f"유사 서비스 조사 모델 검증 오류가 발생했습니다: {str(exception)}") from exception
        except ExternalAPIError:
            raise
        except Exception as exception:
            logger.error(f"유사 서비스 조사 서비스에서 오류가 발생했습니다: {str(exception)}")
            raise AnalysisServiceError(f"유사 서비스 조사 서비스에서 오류가 발생했습니다: {str(exception)}") from exception

    def _generate_prompt(
        self,
        idea: str,
        features: List[str],
    ) -> str:
        return dedent(
            f"""
            다음 비즈니스 아이디어와 유사한 서비스를 JSON 형식으로 제공해주세요:
            비즈니스 아이디어: {idea}
            핵심 기능/요소: {features}
            
            중요: 응답은 반드시 완전한 JSON 배열 형태로만 제공해주세요.
            
            요구사항:
            1. 실제 존재하는 서비스 중 유사도가 높은 상위 5개만 선별해주세요.
            2. 다음 JSON 형식으로 응답해주세요:
            [
              {{
                "name": "서비스 이름",
                "url": "https://www.example.com",
                "description": "300자 내외의 서비스 설명 - 핵심 기능과 특징 포함",
                "targetAudience": "주요 타겟층 설명",
                "tags": ["태그1", "태그2", "태그3", "태그4"],
                "summary": "30자 내외의 서비스 한줄 요약",
                "similarity": 85
              }}
            ]
            
            주의사항:
            - 응답은 위 JSON 배열만 포함해야 합니다
            - 설명 텍스트, 마크다운 등은 절대 포함하지 마세요
            - description은 300자 내외로 간결하게 작성해주세요 (기존 500자에서 단축)
            - tags는 4개로 제한합니다
            - 응답은 한국어로 작성해주세요
            - JSON이 완전히 닫혀있는지 확인해주세요
            """
        ).strip()
