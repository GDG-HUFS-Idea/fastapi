from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.params import Body
from fastapi.responses import StreamingResponse

from app.core.dependency import get_start_overview_analysis_task_usecase, get_watch_overview_analysis_task_progress_usecase
from app.usecase.analysis.start_overview_analysis_task import (
    StartOverviewAnalysisTaskUsecase,
    StartOverviewAnalysisTaskUsecaseDTO,
    StartOverviewAnalysisTaskUsecaseResponse,
)
from app.usecase.analysis.watch_overview_analysis_task_progress import (
    WatchOverviewAnalysisTaskProgressUsecase,
    WatchOverviewAnalysisTaskProgressUsecaseDTO,
)

analysis_router = APIRouter(prefix="/analysis", tags=["analysis"])


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
):
    return await usecase.execute(request, dto)


@analysis_router.get(
    path="/overview/progress",
    response_class=StreamingResponse,
)
async def watch_overview_analysis_task_progress(
    request: Request,
    dto: Annotated[WatchOverviewAnalysisTaskProgressUsecaseDTO, Depends()],
    usecase: WatchOverviewAnalysisTaskProgressUsecase = Depends(get_watch_overview_analysis_task_progress_usecase),
):
    return await usecase.execute(request, dto)
