from abc import ABC
from typing import Optional, TypeVar, Generic, Type
from pydantic import BaseModel, ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError
import secrets
from datetime import timedelta

from app.common.utils import retry
from app.common.exceptions import (
    CacheError,
    CacheConnectionError,
    CacheKeyGenerationError,
    CacheDataCorruptedError,
    CacheSerializationError,
)


T = TypeVar('T', bound=BaseModel)


class BaseCache(ABC, Generic[T]):
    _DATA_CLASS: Type[T]
    _BASE_KEY = ""
    _MAX_KEY_GENERATION_ATTEMPTS = 5

    def __init__(
        self,
        session: Redis,
    ) -> None:
        if not self._BASE_KEY.strip():
            raise ValueError("_BASE_KEY가 설정되지 않았습니다. 하위 클래스에서 정의해야 합니다.")
        if not self._DATA_CLASS:
            raise ValueError("_DATA_CLASS가 설정되지 않았습니다. 하위 클래스에서 정의해야 합니다.")

        self._session = session

    async def set(
        self,
        data: T,
        expire_delta: timedelta,
    ) -> str:
        try:
            # 데이터 직렬화
            data_json = data.model_dump_json()
            expire_time = int(expire_delta.total_seconds())

            # 키 생성 함수 정의
            async def operation():
                key = secrets.token_urlsafe(16)
                full_key = f"{self._BASE_KEY}:{key}"

                is_success = await self._session.set(
                    name=full_key,
                    value=data_json,
                    ex=expire_time,
                    nx=True,
                )

                if is_success:
                    return key
                else:
                    raise CacheKeyGenerationError("중복된 키가 발생했습니다")

            # 재시도 로직으로 키 생성
            return await retry(
                function=operation,
                max_attempts=self._MAX_KEY_GENERATION_ATTEMPTS,
            )

        except ValidationError as exception:
            raise CacheSerializationError(f"데이터 직렬화 중 오류가 발생했습니다: {str(exception)}") from exception
        except ConnectionError as exception:
            raise CacheConnectionError(f"Redis 연결 오류로 캐시 저장에 실패했습니다: {str(exception)}") from exception
        except RedisError as exception:
            raise CacheError(f"Redis 오류로 캐시 저장에 실패했습니다: {str(exception)}") from exception
        except CacheKeyGenerationError:
            raise CacheKeyGenerationError(f"{self._MAX_KEY_GENERATION_ATTEMPTS}번 시도 후에도 고유한 키 생성에 실패했습니다")
        except Exception as exception:
            raise CacheError(f"캐시 저장 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def get(
        self,
        key: str,
    ) -> Optional[T]:
        try:
            full_key = f"{self._BASE_KEY}:{key}"

            # Redis에서 데이터 조회
            data_json = await self._session.get(full_key)
            if data_json is None:
                return None

            # bytes를 문자열로 변환
            if isinstance(data_json, bytes):
                data_json = data_json.decode('utf-8')

            # JSON 데이터를 모델로 파싱
            parsed_data = self._DATA_CLASS.model_validate_json(data_json)
            return parsed_data

        except ConnectionError as exception:
            raise CacheConnectionError(f"Redis 연결 오류로 캐시 조회에 실패했습니다: {str(exception)}") from exception
        except RedisError as exception:
            raise CacheError(f"Redis 오류로 캐시 조회에 실패했습니다: {str(exception)}") from exception
        except ValidationError as exception:
            # 데이터 손상 시 해당 키 삭제 시도
            try:
                await self._session.delete(full_key)  # type: ignore
            except Exception:
                pass  # 삭제 실패해도 원본 예외를 우선시

            raise CacheDataCorruptedError(f"캐시 데이터가 손상되어 파싱할 수 없습니다: {str(exception)}") from exception
        except Exception as exception:
            raise CacheError(f"캐시 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def update(
        self,
        key: str,
        data: T,
        expire_delta: Optional[timedelta] = None,
    ) -> bool:
        try:
            full_key = f"{self._BASE_KEY}:{key}"

            # 키 존재 여부 확인
            existing_data = await self._session.get(full_key)
            if existing_data is None:
                return False

            # 데이터 직렬화
            data_json = data.model_dump_json()

            # TTL 처리 및 데이터 업데이트
            if expire_delta is not None:
                expire_time = int(expire_delta.total_seconds())
                await self._session.set(
                    name=full_key,
                    value=data_json,
                    ex=expire_time,
                )
            else:
                current_ttl = await self._session.ttl(full_key)
                await self._session.set(
                    name=full_key,
                    value=data_json,
                    ex=current_ttl,
                )

            return True

        except ValidationError as exception:
            raise CacheSerializationError(f"데이터 직렬화 중 오류가 발생했습니다: {str(exception)}") from exception
        except ConnectionError as exception:
            raise CacheConnectionError(f"Redis 연결 오류로 캐시 업데이트에 실패했습니다: {str(exception)}") from exception
        except RedisError as exception:
            raise CacheError(f"Redis 오류로 캐시 업데이트에 실패했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise CacheError(f"캐시 업데이트 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def evict(
        self,
        key: str,
    ) -> bool:
        try:
            full_key = f"{self._BASE_KEY}:{key}"

            # 캐시에서 키 삭제
            result = await self._session.delete(full_key)
            return result > 0

        except ConnectionError as exception:
            raise CacheConnectionError(f"Redis 연결 오류로 캐시 삭제에 실패했습니다: {str(exception)}") from exception
        except RedisError as exception:
            raise CacheError(f"Redis 오류로 캐시 삭제에 실패했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise CacheError(f"캐시 삭제 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
