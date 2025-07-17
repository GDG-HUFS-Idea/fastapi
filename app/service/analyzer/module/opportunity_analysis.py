import logging
from textwrap import dedent
from typing import List

from app.common.utils import retry
from app.external.openai import OpenAIClient
from app.common.exceptions import AnalysisServiceError, ExternalAPIError

logger = logging.getLogger(__name__)


class OpportunityAnalysisService:
    _TIMEOUT_SECONDS = 60 * 3
    _TEMPERATURE = 0.7
    _MAX_TOKENS = 1000
    _MAX_ATTEMPTS = 3

    def __init__(
        self,
    ) -> None:
        self._openAI_search_client = OpenAIClient()

    async def execute(
        self,
        idea: str,
        issues: List[str],
        features: List[str],
    ) -> str:
        try:

            async def operation():
                return await self._openAI_search_client.search(
                    input=self._generate_prompt(idea, issues, features),
                    timeout_seconds=self._TIMEOUT_SECONDS,
                    temperature=self._TEMPERATURE,
                    max_output_tokens=self._MAX_TOKENS,
                )

            return await retry(
                function=operation,
                max_attempts=self._MAX_ATTEMPTS,
            )

        except ExternalAPIError:
            raise
        except Exception as exception:
            logger.error(f"기회 분석 서비스에서 오류가 발생했습니다: {str(exception)}")
            raise AnalysisServiceError(f"기회 분석 서비스에서 오류가 발생했습니다: {str(exception)}") from exception

    def _generate_prompt(
        self,
        idea: str,
        issues: List[str],
        features: List[str],
    ) -> str:
        return dedent(
            f"""
            다음 비즈니스 아이디어의 기회 요인과 활용 가능한 지원 사업을 상세히 분석해주세요:

            비즈니스 아이디어: {idea}
            해결하고자 하는 문제: {issues}
            핵심 기능/요소: {features}

            다음 정보를 포함한 분석이 필요합니다:
            1. 시장 기회 요인(최소 3가지): 해당 아이디어가 시장에서 성공할 수 있는 외부 환경 요인
            2. 활용 가능한 정부 지원 사업: 현재 지원 중이거나 곧 시작될 예정인 관련 지원 사업 정보
            3. 공모전 및 액셀러레이터 프로그램: 참여 가능한 공모전, 스타트업 지원 프로그램 등
            4. 각 지원 사업의 신청 시기 및 지원 내용: 구체적인 일정과 지원 금액

            모든 정보는 최신 데이터를 기반으로 구체적으로 작성해주세요.
            응답은 한국어로 작성하고, 출처를 포함해주세요.
            """
        ).strip()
