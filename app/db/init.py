from sqlalchemy import text
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.engine import get_engine
from app.db.model.relation import setup_relation


async def init_db() -> None:
    setup_relation()

    async with get_engine().begin() as conn:
        await conn.run_sync(fn=SQLModel.metadata.create_all)
        await setup_deletion_log_trigger(conn=conn)


async def setup_deletion_log_trigger(conn: AsyncConnection) -> bool:
    with open(
        "app/db/sql/deletion_log_func.sql",
        mode="r",
        encoding="utf-8",
    ) as file:
        func_query = file.read()

    with open(
        "app/db/sql/deletion_log_trigger.sql",
        mode="r",
        encoding="utf-8",
    ) as file:
        trigger_query = file.read()

    await conn.execute(text(func_query))
    await conn.execute(text(trigger_query))

    return True
