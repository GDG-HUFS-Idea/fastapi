import json
import logging
from textwrap import dedent
from typing import List
from pydantic import BaseModel, Field, ValidationError

from app.common.utils import retry, validate_json
from app.external.openai import OpenAIClient
from app.common.exceptions import AnalysisServiceError, ExternalAPIError, JSONValidationError, ModelValidationError

logger = logging.getLogger(__name__)


class _Problem(BaseModel):
    issues: List[str] = Field(alias="identifiedIssues")
    motivation: str = Field(alias="developmentMotivation")


class _Solution(BaseModel):
    features: List[str] = Field(alias="coreElements")
    method: str = Field(alias="methodology")
    deliverable: str = Field(alias="expectedOutcome")


class BusinessCaseExtractionServiceResponse(BaseModel):
    user_id: str
    problem: _Problem
    solution: _Solution


class BusinessCaseExtractionService:
    _TIMEOUT_SECONDS = 60 * 3
    _TEMPERATURE = 0.7
    _MAX_TOKENS = 1000
    _MAX_ATTEMPTS = 3

    def __init__(
        self,
    ) -> None:
        self._openai_client = OpenAIClient()

    async def execute(
        self,
        problem: str,
        solution: str,
    ) -> BusinessCaseExtractionServiceResponse:
        try:

            async def operation():
                content = await self._openai_client.fetch(
                    user_prompt=self._generate_prompt(problem, solution),
                    system_prompt="당신은 입력을 구조화하는 AI 도우미입니다. JSON 포맷만 출력하세요.",
                    timeout_seconds=self._TIMEOUT_SECONDS,
                    temperature=self._TEMPERATURE,
                    max_tokens=self._MAX_TOKENS,
                )
                return BusinessCaseExtractionServiceResponse.model_validate(json.loads(validate_json(content)))

            return await retry(
                function=operation,
                max_attempts=self._MAX_ATTEMPTS,
            )

        except JSONValidationError as exception:  # validate_json에서 발생하는 통합 예외
            raise JSONValidationError(f"비즈니스 케이스 JSON 형식 검증 오류가 발생했습니다: {str(exception)}") from exception
        except ValidationError as exception:
            raise ModelValidationError(f"비즈니스 케이스 모델 검증 오류가 발생했습니다: {str(exception)}") from exception
        except ExternalAPIError:
            raise
        except Exception as exception:
            logger.error(f"비즈니스 케이스 추출 서비스에서 오류가 발생했습니다: {str(exception)}")
            raise AnalysisServiceError(f"비즈니스 케이스 추출 서비스에서 오류가 발생했습니다: {str(exception)}") from exception

    def _generate_prompt(
        self,
        problem: str,
        solution: str,
    ) -> str:
        # NOTE: user id 필요한가?
        return dedent(
            f"""
            다음 사용자 입력을 기반으로 SparkLens 분석을 위한 테스트 데이터 형식으로 구조화해주세요. 
            JSON 형식은 반드시 다음과 같아야 합니다:
            
            {{
                "user_id": "사용자 ID (기본값: testUser)",
                "problem": {{
                    "identifiedIssues": ["문제점1", "문제점2"],
                    "developmentMotivation": "이 문제를 해결하고자 하는 동기"
                }},
                "solution": {{
                    "coreElements": ["핵심 요소1", "핵심 요소2"],
                    "methodology": "핵심 구현 방법",
                    "expectedOutcome": "기대 효과"
                }}
            }}
            
            사용자 입력:
            문제: {problem}
            해결책: {solution}

            반드시 위 JSON 형식에 맞춰 응답해주세요.
            """
        ).strip()
