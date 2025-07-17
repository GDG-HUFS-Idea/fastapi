from functools import lru_cache
from openai import AsyncOpenAI
from openai import APIError, APITimeoutError, RateLimitError, AuthenticationError
import asyncio

from app.core.config import setting
from app.common.exceptions import ExternalAPIError


@lru_cache(maxsize=1)
def _create_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=setting.OPENAI_API_KEY)


class OpenAISearchClient:
    _MODEL = "gpt-4o-mini"
    _TOOLS = {"type": "web_search_preview"}

    async def fetch(
        self,
        user_prompt: str,
        system_prompt: str,
        timeout_seconds: int,
        temperature: float,
        max_tokens: int,
        model: str = _MODEL,
        tools: list = [_TOOLS]
    ) -> str:
        try:
            openai_client = _create_openai_client()

            response = await openai_client.responses.create(
                model=model,
                tools=tools,
                temperature=temperature,
                max_output_tokens=max_tokens,
                timeout=timeout_seconds,
                input=user_prompt
            )

            if not response.output_text:
                raise ExternalAPIError("OpenAI 응답에서 콘텐츠를 찾을 수 없습니다")

            return response.output_text

        except (APITimeoutError, asyncio.TimeoutError) as exception:
            raise ExternalAPIError(f"OpenAI API 요청 타임아웃: {str(exception)}") from exception
        except RateLimitError as exception:
            raise ExternalAPIError(f"OpenAI API 요청 한도 초과: {str(exception)}") from exception
        except AuthenticationError as exception:
            raise ExternalAPIError(f"OpenAI API 인증 실패: {str(exception)}") from exception
        except APIError as exception:
            raise ExternalAPIError(f"OpenAI API 오류: {str(exception)}") from exception
        except ExternalAPIError:
            raise  # 이미 정의된 예외는 그대로 전파
        except Exception as exception:
            raise ExternalAPIError(f"OpenAI 클라이언트 예상치 못한 오류: {str(exception)}") from exception