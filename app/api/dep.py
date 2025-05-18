from redis.asyncio import Redis, from_url
from typing import AsyncGenerator

from app.core.config import env


async def get_redis_session() -> AsyncGenerator[Redis, None]:
    client = await from_url(
        f"redis://{env.redis_host}:{env.redis_port}",
        db=0,
        decode_responses=True,
    )

    try:
        yield client
    finally:
        await client.aclose()
