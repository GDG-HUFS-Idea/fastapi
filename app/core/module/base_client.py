import logging
from typing import Any, Dict, Optional, AsyncGenerator
import httpx
from app.core.config import env
import asyncio
from collections import deque
import time
import json

logger = logging.getLogger(__name__)

class BaseAnalyzer:
    # API 설정
    MODEL = "sonar"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 1000
    
    # API 엔드포인트
    API_BASE_URL = "https://api.perplexity.ai"
    CHAT_ENDPOINT = "/chat/completions"
    
    # 스트림 설정
    STREAM_BUFFER_SIZE = 100
    STREAM_DELAY = 3  # 초

    def __init__(self):
        self.api_key = env.PERPLEXITY_API_KEY
        # API 키 상태 로깅 및 검증
        if not self.api_key or not isinstance(self.api_key, str):
            raise ValueError("PERPLEXITY_API_KEY is not set or invalid")
        
        # API 키 형식 검증 (Bearer 토큰 형식)
        if not self.api_key.startswith("pplx-"):
            logger.warning("PERPLEXITY_API_KEY does not start with 'pplx-'. This might be invalid.")
            
        self.stream_buffer_size = self.STREAM_BUFFER_SIZE
        self.stream_delay = self.STREAM_DELAY
        self.client = httpx.AsyncClient(
            base_url=self.API_BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    def _get_default_params(self) -> Dict[str, Any]:
        """기본 API 호출 파라미터를 반환합니다."""
        return {
            "model": self.MODEL,
            "temperature": self.DEFAULT_TEMPERATURE,
            "max_tokens": self.DEFAULT_MAX_TOKENS
        }

    async def analyze(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            # 기본 파라미터와 사용자 지정 파라미터 병합
            params = {**self._get_default_params(), **kwargs}
            params["messages"] = [
                {"role": "system", "content": "You are a helpful assistant that provides accurate and detailed information."},
                {"role": "user", "content": prompt}
            ]
            
            # 요청 헤더 로깅 (API 키는 마스킹)
            masked_headers = self.client.headers.copy()
            masked_headers["Authorization"] = "Bearer ****" if self.api_key else "Bearer (missing)"
            
            try:
                response = await self.client.post(
                    self.CHAT_ENDPOINT,
                    json=params
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.error("Authentication failed. Please check your API key.")
                    raise ValueError("Invalid API key or authentication failed") from e
                raise
            
            result = response.json()
            if not result or "choices" not in result:
                raise ValueError("Invalid response from Perplexity API")
                
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            raise

    async def stream_analyze(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        try:
            buffer = deque(maxlen=self.stream_buffer_size)
            last_yield_time = time.time()
            chunk_count = 0
            total_chars = 0
            
            logger.info("Starting stream analysis")
            
            # 기본 파라미터와 사용자 지정 파라미터 병합
            params = {**self._get_default_params(), **kwargs}
            params["messages"] = [{"role": "user", "content": prompt}]
            params["stream"] = True
            
            async with self.client.stream(
                "POST",
                self.CHAT_ENDPOINT,
                json=params
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and data["choices"]:
                                chunk = data["choices"][0]
                                if "delta" in chunk and "content" in chunk["delta"]:
                                    text = chunk["delta"]["content"]
                                    current_time = time.time()
                                    chunk_count += 1
                                    total_chars += len(text)
                                    buffer.append(text)
                                    
                                    # 버퍼가 가득 차거나 마지막 yield로부터 일정 시간이 지났을 때 출력
                                    if len(buffer) >= self.stream_buffer_size or (current_time - last_yield_time) >= self.stream_delay:
                                        if buffer:
                                            logger.info("Starting new yield cycle")
                                            output = ''.join(buffer)
                                            yield output
                                            buffer.clear()
                                            last_yield_time = current_time
                                            await asyncio.sleep(self.stream_delay)
                        except json.JSONDecodeError:
                            continue
            
            # 남은 버퍼 내용 출력
            if buffer:
                logger.info("Starting final yield")
                final_output = ''.join(buffer)
                yield final_output
                
        except Exception as e:
            logger.error(f"Stream analysis failed: {str(e)}", exc_info=True)
            raise

    async def close(self):
        """클라이언트 연결을 종료합니다."""
        await self.client.aclose()
