from datetime import datetime
from typing import List, cast
from fastapi import Query
from pydantic import BaseModel

from app.repository.project import ProjectRepository
from app.service.auth.jwt import Payload
from app.common.exceptions import NotFoundException, RepositoryError, UsecaseException, InternalServerException


class RetrieveMyProjectsUsecaseDTO(BaseModel):
    offset: int = Query(ge=0)
    limit: int = Query(ge=1, le=100)


class _Project(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


class RetrieveMyProjectsUsecaseResponse(BaseModel):
    projects: List[_Project]


class RetrieveMyProjectsUsecase:
    def __init__(
        self,
        project_repository: ProjectRepository,
    ) -> None:
        self._project_repository = project_repository

    async def execute(
        self,
        dto: RetrieveMyProjectsUsecaseDTO,
        payload: Payload,
    ) -> RetrieveMyProjectsUsecaseResponse:
        try:
            projects = await self._project_repository.find_many_by_user_id(user_id=payload.id, limit=dto.limit, offset=dto.offset)

            if not projects:
                raise NotFoundException("해당 사용자의 프로젝트가 존재하지 않습니다.")

            return RetrieveMyProjectsUsecaseResponse(
                projects=[
                    _Project(
                        id=cast(int, project.id),
                        name=project.name,
                        status=project.status.value,
                        created_at=project.created_at,
                        updated_at=project.updated_at,
                    )
                    for project in projects
                ]
            )

        except RepositoryError as exception:
            raise InternalServerException(str(exception)) from exception
        except UsecaseException:
            raise
        except Exception as exception:
            raise InternalServerException(f"예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
