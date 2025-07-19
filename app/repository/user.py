from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.user import User
from app.common.exceptions import UserRepositoryError


class UserRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def find_by_email(
        self,
        email: str,
    ) -> Optional[User]:
        try:
            query = select(User).where(User.email == email)
            result = await self._session.exec(query)
            return result.first()

        except Exception as exception:
            raise UserRepositoryError("사용자 조회 중 오류가 발생했습니다.") from exception

    async def save(
        self,
        user: User,
    ) -> None:
        try:
            self._session.add(user)
            await self._session.flush()
            await self._session.refresh(user)

        except Exception as exception:
            raise UserRepositoryError("사용자 저장 중 오류가 발생했습니다.") from exception
