from datetime import datetime
from typing import List, Optional
from fastapi import Query
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.model.term import Term
from app.repo.term import TermRepo
from app.util.enum import TermType
from app.util.exception import DBServerException, DataNotFoundException


class RetrieveTermsServiceDTO(BaseModel):
    ids: List[int] = Field(Query(description="약관 ID 목록"))


class TermResponse(BaseModel):
    id: int
    title: str
    type: TermType
    content: str
    is_required: bool
    created_at: datetime
    updated_at: datetime


class RetrieveTermsServiceResponse(BaseModel):
    terms: List[TermResponse]
    missing_ids: Optional[List[int]] = None


class RetrieveTermsService:
    def __init__(self, pg_session: AsyncSession):
        self.term_repo = TermRepo(pg_session)

    async def exec(
        self, dto: RetrieveTermsServiceDTO
    ) -> RetrieveTermsServiceResponse:
        terms = await self.retrieve_terms(dto.ids)
        not_found_ids = self.extract_missing_ids(dto.ids, terms)

        return RetrieveTermsServiceResponse(
            terms=[term.model_dump() for term in terms],  # type: ignore
            missing_ids=not_found_ids,
        )

    async def retrieve_terms(self, ids: List[int]) -> List[Term]:
        """
        ids에 해당하는 약관 조회
        """
        try:
            terms = await self.term_repo.find_many_by_ids(ids)
        except Exception as exc:
            raise DBServerException

        if not len(terms):
            raise DataNotFoundException

        return terms

    def extract_missing_ids(
        self, requested_ids: List[int], terms: List[Term]
    ) -> Optional[List[int]]:
        """
        요청한 약관 ID에서 찾지 못한 ID 목록을 반환
        """
        found_ids = {term.id for term in terms}
        not_found_ids = list(set(requested_ids) - found_ids)

        if len(not_found_ids) > 0:
            return not_found_ids
