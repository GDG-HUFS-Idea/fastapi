from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.model.term_agreement import TermAgreement


class TermAgreementRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_many(self, term_agreements: List[TermAgreement]) -> None:
        self.session.add_all(term_agreements)
        await self.session.flush()
        for term_agreement in term_agreements:
            await self.session.refresh(term_agreement)
