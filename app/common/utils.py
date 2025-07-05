import asyncio
import json
import logging
import re
from typing import Callable, TypeVar, Awaitable

from app.common.exceptions import JSONValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry(
    function: Callable[[], Awaitable[T]],
    max_attempts: int,
) -> T:
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return await function()

        except Exception as exception:
            logger.warning(f"시도 {attempt + 1}/{max_attempts} 실패: {str(exception)}")
            last_exception = exception

            if attempt < max_attempts - 1:
                wait_time = attempt**2
                await asyncio.sleep(wait_time)
                continue

    assert last_exception is not None
    raise last_exception
