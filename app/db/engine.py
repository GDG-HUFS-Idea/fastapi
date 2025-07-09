import os
from functools import lru_cache
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import env


@lru_cache(maxsize=1)
def get_engine():
    return create_async_engine(
        url=get_pg_url(),
        echo=True,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        max_overflow=10,
    )


@lru_cache(maxsize=1)
def get_session_maker():
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


def get_pg_url():
    if os.path.exists("/.dockerenv"):
        host = env.pg_host
    else:
        host = "localhost"
    return f"postgresql+asyncpg://{env.pg_user}:{env.pg_pw}@{host}:{env.pg_port}/{env.pg_db}"
