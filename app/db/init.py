from sqlmodel import SQLModel

from app.db.engine import get_engine
from app.db.model.relation import setup_relation


async def init_db() -> None:
    setup_relation()

    async with get_engine().begin() as conn:
        await conn.run_sync(fn=SQLModel.metadata.create_all)
