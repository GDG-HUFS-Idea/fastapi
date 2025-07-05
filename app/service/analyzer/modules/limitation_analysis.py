import logging
from textwrap import dedent
from typing import List

from app.common.utils import retry
from app.external.perplexity import PerplexityClient
from app.common.exceptions import AnalysisServiceError, ExternalAPIError

logger = logging.getLogger(__name__)


class LimitationAnalysisService:
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
            logger.error(f"한계점 분석 서비스에서 오류가 발생했습니다: {str(exception)}")
            raise AnalysisServiceError(f"한계점 분석 서비스에서 오류가 발생했습니다: {str(exception)}") from exception

    def _generate_prompt(
        self,
        idea: str,
        issues: List[str],
        features: List[str],
    ) -> str:
        return dedent(
            f"""
            다음 비즈니스 아이디어의 사업화 과정에서 발생할 수 있는 잠재적 한계점과 위험 요소를 상세히 분석해주세요:

            비즈니스 아이디어: {idea}
            해결하고자 하는 문제: {issues}
            핵심 기능/요소: {features}

            다음 정보를 포함한 분석이 필요합니다:
            1. 법률적 규제 및 제약(구체적인 법률명과 조항 포함)
            2. 특허 관련 이슈 및 지적재산권 문제(유사 특허 존재 여부)
            3. 시장 진입 장벽(기존 경쟁사, 초기 투자 요구 등)
            4. 기술적 제약 및 구현 난이도
            5. 잠재적 고객 수용성 문제

            각 항목별로 구체적인 사례와 데이터를 포함하여 분석해주세요.
            응답은 한국어로 작성하고, 출처를 포함해주세요.
            """
        ).strip()
