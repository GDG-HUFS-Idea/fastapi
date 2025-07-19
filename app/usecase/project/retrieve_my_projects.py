from datetime import datetime
from typing import List, cast
from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ProjectStatus
from app.repository.project import ProjectRepository
from app.service.auth.jwt import Payload
from app.common.exceptions import NotFoundException, RepositoryError, UsecaseException, InternalServerException


class RetrieveMyProjectsUsecaseDTO(BaseModel):
    offset: int = Field(Query(ge=0), description="조회 시작 위치")
    limit: int = Field(Query(ge=1, le=100), description="조회할 프로젝트 개수")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"offset": 0, "limit": 50},
                {"offset": 20, "limit": 10},
            ]
        }
    )


class _Project(BaseModel):
    id: int = Field(description="프로젝트 ID")
    name: str = Field(description="프로젝트 이름")
    status: ProjectStatus = Field(description="프로젝트 상태")
    created_at: datetime = Field(description="프로젝트 생성 일시")
    updated_at: datetime = Field(description="프로젝트 최종 수정 일시")


class RetrieveMyProjectsUsecaseResponse(BaseModel):
    projects: List[_Project] = Field(description="조회된 프로젝트 목록")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "projects": [
                        {
                            "id": 1,
                            "name": "자연재해 대비 물품 판매",
                            "status": "analyzed",
                            "created_at": "2025-07-11T06:19:05.851264Z",
                            "updated_at": "2025-07-11T06:20:38.318675Z",
                        },
                        {
                            "id": 2,
                            "name": "온라인 교육 플랫폼",
                            "status": "in_progress",
                            "created_at": "2025-07-10T15:30:22.123456Z",
                            "updated_at": "2025-07-11T09:45:15.987654Z",
                        },
                    ]
                }
            ]
        }
    )


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
                        status=project.status,
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
