from redis.asyncio import Redis, from_url
from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import env
from app.db.engine import get_session_maker


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


async def get_pg_session() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()

    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
