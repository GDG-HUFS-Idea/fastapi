from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import os
from functools import lru_cache
from textwrap import dedent
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncConnection, AsyncEngine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import setting
from app.domain.relation import setup_relations


async def init_database() -> None:
    setup_relations()

    async with get_engine().begin() as connection:
        await connection.run_sync(fn=SQLModel.metadata.create_all)
        await setup_deletion_log_trigger(connection=connection)
        await setup_term_dummy_data(connection=connection)


@asynccontextmanager
async def get_static_db_session() -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    return create_async_engine(
        url=get_pg_url(),
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        max_overflow=10,
    )


def get_pg_url() -> str:
    if os.path.exists("/.dockerenv"):
        host = setting.PG_HOST
    else:
        host = "localhost"
    return f"postgresql+asyncpg://{setting.PG_USER}:{setting.PG_PW}@{host}:{setting.PG_PORT}/{setting.PG_DB}"


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker:
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def setup_deletion_log_trigger(
    connection: AsyncConnection,
) -> None:
    func_query = dedent(
        """
        CREATE OR REPLACE FUNCTION deletion_log_trigger()
        RETURNS TRIGGER AS $$
        DECLARE
            user_id INTEGER;
            record_json JSONB;
        BEGIN
            user_id := COALESCE(
                NULLIF(current_setting('session.user_id', TRUE), '')::INTEGER, 
                -1
            );
            record_json := to_jsonb(OLD);

            INSERT INTO deletion_log (
                deleted_by,
                table_name,
                record_id,
                record_data,
                deleted_at
            ) VALUES (
                user_id,
                TG_TABLE_NAME,
                OLD.id,
                record_json,
                NOW()
            );

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
        """
    ).strip()

    trigger_query = dedent(
        """
        DO $$
        DECLARE
            tbl_name text;
            trigger_name text;
        BEGIN
            FOR tbl_name IN 
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename != 'deletion_log'
                AND tablename NOT LIKE 'alembic_%'
            LOOP
                trigger_name := tbl_name || '_deletion_log_trigger';
                EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', 
                                trigger_name, tbl_name);
                EXECUTE format('CREATE TRIGGER %I 
                                BEFORE DELETE ON %I
                                FOR EACH ROW
                                EXECUTE FUNCTION deletion_log_trigger()', 
                                trigger_name, tbl_name);
            END LOOP;
        END $$;
        """
    ).strip()

    await connection.execute(text(func_query))
    await connection.execute(text(trigger_query))


from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import os
from functools import lru_cache
from textwrap import dedent
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncConnection, AsyncEngine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import setting
from app.domain.relation import setup_relations


async def init_database() -> None:
    setup_relations()

    async with get_engine().begin() as connection:
        await connection.run_sync(fn=SQLModel.metadata.create_all)
        await setup_deletion_log_trigger(connection=connection)
        await setup_term_dummy_data(connection=connection)


@asynccontextmanager
async def get_static_db_session() -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    return create_async_engine(
        url=get_pg_url(),
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        max_overflow=10,
    )


def get_pg_url() -> str:
    if os.path.exists("/.dockerenv"):
        host = setting.PG_HOST
    else:
        host = "localhost"
    return f"postgresql+asyncpg://{setting.PG_USER}:{setting.PG_PW}@{host}:{setting.PG_PORT}/{setting.PG_DB}"


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker:
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def setup_deletion_log_trigger(
    connection: AsyncConnection,
) -> None:
    func_query = dedent(
        """
        CREATE OR REPLACE FUNCTION deletion_log_trigger()
        RETURNS TRIGGER AS $$
        DECLARE
            user_id INTEGER;
            record_json JSONB;
        BEGIN
            user_id := COALESCE(
                NULLIF(current_setting('session.user_id', TRUE), '')::INTEGER, 
                -1
            );
            record_json := to_jsonb(OLD);

            INSERT INTO deletion_log (
                deleted_by,
                table_name,
                record_id,
                record_data,
                deleted_at
            ) VALUES (
                user_id,
                TG_TABLE_NAME,
                OLD.id,
                record_json,
                NOW()
            );

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
        """
    ).strip()

    trigger_query = dedent(
        """
        DO $$
        DECLARE
            tbl_name text;
            trigger_name text;
        BEGIN
            FOR tbl_name IN 
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename != 'deletion_log'
                AND tablename NOT LIKE 'alembic_%'
            LOOP
                trigger_name := tbl_name || '_deletion_log_trigger';
                EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', 
                                trigger_name, tbl_name);
                EXECUTE format('CREATE TRIGGER %I 
                                BEFORE DELETE ON %I
                                FOR EACH ROW
                                EXECUTE FUNCTION deletion_log_trigger()', 
                                trigger_name, tbl_name);
            END LOOP;
        END $$;
        """
    ).strip()

    await connection.execute(text(func_query))
    await connection.execute(text(trigger_query))


async def setup_term_dummy_data(
    connection: AsyncConnection,
) -> None:
    terms_data = [
        {
            'type': 'TERMS_OF_SERVICE',
            'is_required': True,
            'is_active': True,
            'title': '서비스 이용약관',
            'content': '본 약관은 회사가 제공하는 서비스의 이용 조건을 규정합니다.',
            'version': '1.0',
        },
        {
            'type': 'PRIVACY_POLICY',
            'is_required': True,
            'is_active': True,
            'title': '개인정보처리방침',
            'content': '회사는 개인정보보호법에 따라 이용자의 개인정보를 보호합니다.',
            'version': '1.0',
        },
        {
            'type': 'MARKETING',
            'is_required': False,
            'is_active': True,
            'title': '마케팅 정보 수신 동의',
            'content': '회사는 이용자에게 마케팅 정보를 발송할 수 있습니다.',
            'version': '1.0',
        },
    ]

    for term_data in terms_data:
        insert_query = text(
            """
            INSERT INTO term (type, is_required, is_active, title, content, version, created_at)
            SELECT :type, :is_required, :is_active, :title, :content, :version, NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM term WHERE type = :type
            )
        """
        )

        await connection.execute(insert_query, term_data)
