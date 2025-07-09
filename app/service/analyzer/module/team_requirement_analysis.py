import logging
from textwrap import dedent
from typing import List

from app.common.utils import retry
from app.external.perplexity import PerplexityClient
from app.common.exceptions import AnalysisServiceError, ExternalAPIError

logger = logging.getLogger(__name__)


class TeamRequirementAnalysisService:
    _TIMEOUT_SECONDS = 60 * 3
    _TEMPERATURE = 0.7
    _MAX_TOKENS = 1000
    _MAX_ATTEMPTS = 3

    def __init__(self) -> None:
        self._perplexity_client = PerplexityClient()

    async def execute(
        self,
        idea: str,
        issues: List[str],
        features: List[str],
    ) -> str:
        try:

            async def operation():
                return await self._perplexity_client.fetch(
                    user_prompt=self._generate_prompt(idea, issues, features),
                    system_prompt="You are a helpful assistant that provides accurate and detailed information.",
                    timeout_seconds=self._TIMEOUT_SECONDS,
                    temperature=self._TEMPERATURE,
                    max_tokens=self._MAX_TOKENS,
                )

            return await retry(
                function=operation,
                max_attempts=self._MAX_ATTEMPTS,
            )

        except ExternalAPIError:
            raise
        except Exception as exception:
            logger.error(f"팀 구성 요구 사항 분석 서비스에서 오류가 발생했습니다: {str(exception)}")
            raise AnalysisServiceError(f"팀 구성 요구 사항 분석 서비스에서 오류가 발생했습니다: {str(exception)}") from exception

    def _generate_prompt(
        self,
        idea: str,
        issues: List[str],
        features: List[str],
    ) -> str:
        return dedent(
            f"""
            다음 비즈니스 아이디어를 성공적으로 실현하기 위해 필요한 팀 구성을 상세히 분석해주세요:

            비즈니스 아이디어: {idea}
            해결하고자 하는 문제: {issues}
            핵심 기능/요소: {features}

            다음 정보를 포함한 분석이 필요합니다:
            1. 필요한 직책/역할(최소 3가지): 구체적인 직함과 역할
            2. 각 역할별 필요 역량 및 경험: 구체적인 기술, 지식, 자격 요건
            3. 담당해야 할 업무 범위: 상세한 업무 내용
            4. 팀 구성의 우선순위: 초기 스타트업 단계에서 먼저 영입해야 할 역할 순서
            
            최소 필요 인력부터 이상적인 팀 구성까지 단계별로 제안해주세요.
            응답은 한국어로 작성하고, 출처를 포함해주세요.
            """
        ).strip()
