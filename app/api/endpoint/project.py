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
    response_model=RetrieveMyProjectsUsecaseResponse,
)
async def retrieve_projects(
    dto: Annotated[RetrieveMyProjectsUsecaseDTO, Depends()],
    usecase: RetrieveMyProjectsUsecase = Depends(get_retrieve_my_projects_usecase),
    payload: Payload = Depends(get_current_user),
):
    return await usecase.execute(dto, payload)
