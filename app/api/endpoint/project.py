from typing import Annotated
from fastapi import APIRouter, Depends

from app.core.dependency import (
    get_current_user,
    get_retrieve_my_projects_usecase,
)
from app.service.auth.jwt import Payload
from app.usecase.project.retrieve_my_projects import (
    RetrieveMyProjectsUsecase,
    RetrieveMyProjectsUsecaseDTO,
    RetrieveMyProjectsUsecaseResponse,
)

project_router = APIRouter(prefix="/projects", tags=["project"])


@project_router.get(
    path="",
    status_code=200,
    response_model=RetrieveMyProjectsUsecaseResponse,
    response_model_exclude_none=True,
    responses={
        200: {"description": "내 프로젝트 목록 조회 성공"},
        401: {"description": "인증되지 않은 사용자"},
        404: {"description": "해당 사용자의 프로젝트가 존재하지 않는 경우"},
        422: {"description": "검증 오류 - offset 또는 limit 파라미터가 유효하지 않은 경우"},
        500: {"description": "서버 내부 오류 - 저장소 오류 또는 예상치 못한 오류 발생"},
    },
)
async def retrieve_projects(
    dto: Annotated[RetrieveMyProjectsUsecaseDTO, Depends()],
    usecase: RetrieveMyProjectsUsecase = Depends(get_retrieve_my_projects_usecase),
    payload: Payload = Depends(get_current_user),
):
    return await usecase.execute(dto, payload)
