import logging

from app.common.utils import retry
from app.external.openai import OpenAIClient
from app.common.exceptions import AnalysisServiceError, ExternalAPIError

logger = logging.getLogger(__name__)


class IdeaSummationService:
    _TIMEOUT_SECONDS = 60 * 2
    _TEMPERATURE = 0.7
    _MAX_TOKENS = 1000
    _MAX_ATTEMPTS = 3

    def __init__(self) -> None:
        self._openai_client = OpenAIClient()

    async def execute(
        self,
        problem: str,
        solution: str,
    ) -> str:
        try:

            async def operation():
                return await self._openai_client.fetch(
                    user_prompt=f"문제: {problem} 해결책: {solution}",
                    system_prompt="아이디어를 5단어 이내 한국어로 요약해주세요.",
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
            logger.error(f"아이디어 요약 서비스에서 오류가 발생했습니다: {str(exception)}")
            raise AnalysisServiceError(f"아이디어 요약 서비스에서 오류가 발생했습니다: {str(exception)}") from exception
