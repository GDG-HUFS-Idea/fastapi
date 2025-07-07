from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.domain.project_idea import ProjectIdea
from app.common.exceptions import ProjectIdeaRepositoryError


class ProjectIdeaRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save(
        self,
        idea: ProjectIdea,
    ) -> None:
        try:
            self._session.add(idea)
            await self._session.flush()
            await self._session.refresh(idea)

        except SQLAlchemyError as exception:
            raise ProjectIdeaRepositoryError(f"프로젝트 아이디어 저장 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise ProjectIdeaRepositoryError(f"프로젝트 아이디어 저장 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def find_many_by_user_id(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> List[ProjectIdea]:
        try:
            query = select(ProjectIdea).where(ProjectIdea.user_id == user_id).limit(limit).offset(offset).order_by(ProjectIdea.created_at.desc())  # type: ignore
            result = await self._session.exec(query)
            return list(result.all())

        except SQLAlchemyError as exception:
            raise ProjectIdeaRepositoryError(f"프로젝트 아이디어 조회 쿼리 실행 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise ProjectIdeaRepositoryError(f"프로젝트 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
