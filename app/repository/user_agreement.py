from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.domain.user_agreement import UserAgreement
from app.common.exceptions import UserAgreementRepositoryError


class UserAgreementRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save_batch(
        self,
        term_agreements: List[UserAgreement],
    ) -> List[UserAgreement]:
        try:
            self._session.add_all(term_agreements)
            await self._session.flush()

            for term_agreement in term_agreements:
                await self._session.refresh(term_agreement)

            return term_agreements

        except SQLAlchemyError as exception:
            raise UserAgreementRepositoryError(f"UserAgreement 배치 저장 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise UserAgreementRepositoryError(
                f"UserAgreement 배치 저장 중 예상치 못한 오류가 발생했습니다: {str(exception)}"
            ) from exception
