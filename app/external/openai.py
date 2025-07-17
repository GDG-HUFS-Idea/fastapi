from functools import lru_cache
from typing import AsyncIterator
from openai import AsyncOpenAI
from openai import APIError, APITimeoutError, RateLimitError, AuthenticationError
import asyncio

from app.core.config import setting
from app.common.exceptions import ExternalAPIError


@lru_cache(maxsize=1)
def _create_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=setting.OPENAI_API_KEY)


class OpenAIClient:
    _MODEL = "gpt-4o-mini"

    async def fetch(
        self,
        user_prompt: str,
        system_prompt: str,
        timeout_seconds: int,
        temperature: float,
        max_tokens: int,
        model: str = _MODEL,
    ) -> str:
        try:
            openai_client = _create_openai_client()

            response = await openai_client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_seconds,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )

            if not response.choices or not response.choices[0].message.content:
                raise ExternalAPIError("OpenAI 응답에서 콘텐츠를 찾을 수 없습니다")

            return response.choices[0].message.content.strip()

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

    async def stream(
        self,
        user_prompt: str,
        system_prompt: str,
        timeout_seconds: int,
        temperature: float,
        max_tokens: int,
        model: str = _MODEL,
    ) -> AsyncIterator[str]:
        try:
            openai_client = _create_openai_client()

            stream = await openai_client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_seconds,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                elif chunk.choices[0].finish_reason:
                    break

        except (APITimeoutError, asyncio.TimeoutError) as exception:
            raise ExternalAPIError(f"OpenAI API 스트림 타임아웃: {str(exception)}") from exception
        except RateLimitError as exception:
            raise ExternalAPIError(f"OpenAI API 요청 한도 초과: {str(exception)}") from exception
        except AuthenticationError as exception:
            raise ExternalAPIError(f"OpenAI API 인증 실패: {str(exception)}") from exception
        except APIError as exception:
            raise ExternalAPIError(f"OpenAI API 스트림 오류: {str(exception)}") from exception
        except (IndexError, AttributeError) as exception:
            raise ExternalAPIError(f"OpenAI 스트림 응답 파싱 오류: {str(exception)}") from exception
        except Exception as exception:
            raise ExternalAPIError(f"OpenAI 스트림 예상치 못한 오류: {str(exception)}") from exception

    async def search(
        self,
        input: str,
        timeout_seconds: int,
        temperature: float,
        max_output_tokens: int,
        model: str = _MODEL,
        tools: list = {"type": "web_search_preview"}
    ) -> str:
        try:
            openai_client = _create_openai_client()

            response = await openai_client.responses.create(
                model=model,
                tools=tools,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                timeout=timeout_seconds,
                input=input
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