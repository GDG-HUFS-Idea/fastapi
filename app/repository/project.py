from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.domain.project import Project
from app.common.exceptions import ProjectRepositoryError


class ProjectRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save(
        self,
        project: Project,
    ) -> None:
        try:
            self._session.add(project)
            await self._session.flush()
            await self._session.refresh(project)

        except SQLAlchemyError as exception:
            raise ProjectRepositoryError(f"프로젝트 저장 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise ProjectRepositoryError(f"프로젝트 저장 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def find_many_by_user_id(
        self,
        user_id: int,
        limit: int,
        offset: int,
    ) -> List[Project]:
        try:
            query = select(Project).where(Project.user_id == user_id).limit(limit).offset(offset).order_by(Project.created_at.desc())  # type: ignore
            result = await self._session.exec(query)
            return list(result.all())

        except SQLAlchemyError as exception:
            raise ProjectRepositoryError(f"사용자({user_id})의 프로젝트 조회 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise ProjectRepositoryError(f"프로젝트 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
