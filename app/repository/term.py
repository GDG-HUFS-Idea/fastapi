from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.domain.term import Term
from app.common.exceptions import TermRepositoryError


class TermRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def find_many_by_ids(
        self,
        ids: List[int],
    ) -> List[Term]:
        try:
            query = select(Term).where(Term.id.in_(ids))  # type: ignore
            result = await self._session.exec(query)
            return list(result.all())

        except Exception as exception:
            raise TermRepositoryError("Term 조회 중 오류가 발생했습니다.") from exception

    async def find_active_terms(
        self,
    ) -> List[Term]:
        try:
            query = select(Term).where(Term.is_active.is_(True))  # type: ignore
            result = await self._session.exec(query)
            return list(result.all())

        except Exception as exception:
            raise TermRepositoryError("활성 Term 조회 중 오류가 발생했습니다.") from exception

    async def save_batch(
        self,
        terms: List[Term],
    ) -> List[Term]:
        try:
            for term in terms:
                self._session.add(term)

            await self._session.flush()

            for term in terms:
                await self._session.refresh(term)

            return terms

        except Exception as exception:
            raise TermRepositoryError("Term 배치 저장 중 오류가 발생했습니다.") from exception
