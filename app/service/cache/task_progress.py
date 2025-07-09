from datetime import timedelta
from typing import Optional
from pydantic import BaseModel, ValidationError
from redis.asyncio import Redis

from app.common.enums import TaskStatus
from app.service.cache.base import BaseCache
from app.common.exceptions import CacheError, CacheSerializationError


class TaskProgress(BaseModel):
    status: TaskStatus
    progress: float
    message: str
    host: str
    user_id: Optional[int] = None
    start_time: float


class TaskProgressCache(BaseCache[TaskProgress]):
    _BASE_KEY = "task_progress"
    _DATA_CLASS = TaskProgress

    def __init__(
        self,
        session: Redis,
    ) -> None:
        super().__init__(session)

    async def update_partial(
        self,
        key: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        host: Optional[str] = None,
        start_time: Optional[float] = None,
        expire_delta: Optional[timedelta] = None,
    ) -> bool:
        try:
            # 기존 데이터 조회
            current_data = await self.get(key)
            if current_data is None:
                return False

            # 부분 업데이트
            updated_data = TaskProgress(
                status=status if status is not None else current_data.status,
                progress=progress if progress is not None else current_data.progress,
                message=message if message is not None else current_data.message,
                host=host if host is not None else current_data.host,
                user_id=current_data.user_id,
                start_time=start_time if start_time is not None else current_data.start_time,
            )

            return await super().update(key, updated_data, expire_delta)

        except ValidationError as exception:
            raise CacheSerializationError(f"TaskProgress 데이터 생성 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise CacheError(f"부분 캐시 업데이트 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
