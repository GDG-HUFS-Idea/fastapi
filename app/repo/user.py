from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.model.user import User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)

        result = await self.session.exec(query)
        record = result.first()

        return record

    async def save(self, user: User) -> None:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
