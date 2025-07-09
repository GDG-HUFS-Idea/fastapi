from redis.asyncio import Redis, from_url

from app.core.config import setting


_client = None


async def get_redis_connection() -> Redis:
    global _client

    if _client is None:
        _client = await from_url(
            f"redis://{setting.REDIS_HOST}:{setting.REDIS_PORT}",
            db=0,
            decode_responses=True,
            socket_keepalive=True,
        )
    try:
        await _client.ping()
    except (ConnectionError, TimeoutError):
        _client = await from_url(
            f"redis://{setting.REDIS_HOST}:{setting.REDIS_PORT}",
            db=0,
            decode_responses=True,
            socket_keepalive=True,
        )
        await _client.ping()

    return _client
