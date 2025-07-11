from typing import Annotated
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.dependency import (
    get_current_user,
    get_retrieve_overview_analysis_usecase,
    get_start_overview_analysis_task_usecase,
    get_watch_overview_analysis_task_progress_usecase,
)
from app.service.auth.jwt import Payload
from app.usecase.analysis.start_overview_analysis_task import (
    StartOverviewAnalysisTaskUsecase,
    StartOverviewAnalysisTaskUsecaseDTO,
    StartOverviewAnalysisTaskUsecaseResponse,
)
from app.usecase.analysis.watch_overview_analysis_task_progress import (
    WatchOverviewAnalysisTaskProgressUsecase,
    WatchOverviewAnalysisTaskProgressUsecaseDTO,
)
from app.service.auth.jwt import Payload
from app.usecase.analysis.retrieve_overview_analysis import (
    RetrieveOverviewAnalysisUsecase,
    RetrieveOverviewAnalysisUsecaseDTO,
    RetrieveOverviewAnalysisUsecaseResponse,
)

analysis_router = APIRouter(prefix="/analyses", tags=["analysis"])


@analysis_router.post(
    path="/overview",
    status_code=200,
    response_model=StartOverviewAnalysisTaskUsecaseResponse,
    response_model_exclude_none=True,
)
async def start_overview_analysis_task(
    request: Request,
    dto: Annotated[StartOverviewAnalysisTaskUsecaseDTO, Body()],
    usecase: StartOverviewAnalysisTaskUsecase = Depends(get_start_overview_analysis_task_usecase),
    payload: Payload = Depends(get_current_user),
):
    return await usecase.execute(request, dto, payload)


@analysis_router.get(
    path="/overview/progress",
    response_class=StreamingResponse,
)
async def watch_overview_analysis_task_progress(
    request: Request,
    dto: Annotated[WatchOverviewAnalysisTaskProgressUsecaseDTO, Depends()],
    usecase: WatchOverviewAnalysisTaskProgressUsecase = Depends(get_watch_overview_analysis_task_progress_usecase),
    payload: Payload = Depends(get_current_user),
):
    return await usecase.execute(request, dto, payload)


@analysis_router.get(
    path="/overview",
    response_model=RetrieveOverviewAnalysisUsecaseResponse,
)
async def retrieve_overview_analysis(
    dto: Annotated[RetrieveOverviewAnalysisUsecaseDTO, Depends()],
    usecase: RetrieveOverviewAnalysisUsecase = Depends(get_retrieve_overview_analysis_usecase),
    payload: Payload = Depends(get_current_user),
):
    return await usecase.execute(dto, payload)
