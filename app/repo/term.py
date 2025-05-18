from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.db.model.term import Term
from app.util.enum import TermType


class TermRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_many_by_ids(self, ids: List[int]) -> List[Term]:
        query = select(Term).where(Term.id.in_(ids))  # type: ignore

        result = await self.session.exec(query)
        records = result.all()

        return list(records)

    async def find_many_by_types(self, types: List[TermType]) -> List[Term]:
        query = (
            select(Term)
            .where(Term.type.in_(types))  # type: ignore
            .distinct(Term.type)  # type: ignore
            .order_by(
                Term.type,
                Term.created_at.desc(),  # type: ignore
                Term.id.desc(),  # type: ignore
            )
        )

        result = await self.session.exec(query)
        records = result.all()

        return list(records)
