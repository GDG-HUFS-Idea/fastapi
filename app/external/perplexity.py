from httpx import AsyncClient, HTTPStatusError, TimeoutException, ConnectError
import json

from app.core.config import setting
from app.common.exceptions import ExternalAPIError


class PerplexityClient:
    _MODEL = "sonar"
    _API_BASE_URL = "https://api.perplexity.ai"
    _CHAT_ENDPOINT = "/chat/completions"

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
            async with AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    f"{self._API_BASE_URL}{self._CHAT_ENDPOINT}",
                    headers={
                        "Authorization": f"Bearer {setting.PERPLEXITY_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt,
                            },
                            {
                                "role": "user",
                                "content": user_prompt,
                            },
                        ],
                    },
                )

                response.raise_for_status()
                response_data = response.json()

                if "choices" not in response_data or not response_data["choices"]:
                    raise ExternalAPIError("Perplexity 응답에서 콘텐츠를 찾을 수 없습니다")

                return response_data["choices"][0]["message"]["content"].strip()

        except TimeoutException as exception:
            raise ExternalAPIError(f"Perplexity API 요청 타임아웃: {str(exception)}") from exception
        except ConnectError as exception:
            raise ExternalAPIError(f"Perplexity API 연결 실패: {str(exception)}") from exception
        except HTTPStatusError as exception:
            if exception.response.status_code == 401:
                raise ExternalAPIError(f"Perplexity API 인증 실패: {str(exception)}") from exception
            elif exception.response.status_code == 429:
                raise ExternalAPIError(f"Perplexity API 요청 한도 초과: {str(exception)}") from exception
            else:
                raise ExternalAPIError(f"Perplexity API HTTP 오류 ({exception.response.status_code}): {str(exception)}") from exception
        except json.JSONDecodeError as exception:
            raise ExternalAPIError(f"Perplexity API 응답 파싱 실패: {str(exception)}") from exception
        except (KeyError, IndexError) as exception:
            raise ExternalAPIError(f"Perplexity API 응답 구조 오류: {str(exception)}") from exception
        except ExternalAPIError:
            raise  # 이미 정의된 예외는 그대로 전파
        except Exception as exception:
            raise ExternalAPIError(f"Perplexity 클라이언트 예상치 못한 오류: {str(exception)}") from exception
