from typing import Annotated, Any, Dict
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import StreamingResponse

from app.common.enums import TaskStatus
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
from app.usecase.analysis.blocks9_analysis import Blocks9AnalysisUsecase
from app.service.analyzer.dto.second_stage import Blocks9Input

analysis_router = APIRouter(prefix="/analyses", tags=["analysis"])


@analysis_router.post(
    path="/overview",
    status_code=200,
    response_model=StartOverviewAnalysisTaskUsecaseResponse,
    response_model_exclude_none=True,
    responses={
        200: {"description": "개요 분석 작업 시작 성공 - 작업 ID 반환, 백그라운드에서 분석 진행"},
        401: {"description": "인증 실패 - 클라이언트 호스트 정보를 조회할 수 없는 경우"},
        422: {"description": "검증 오류 - 문제나 솔루션 설명이 유효하지 않은 경우"},
        500: {"description": "서버 내부 오류 - 캐시 오류 또는 예상치 못한 오류 발생"},
    },
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
    responses={
        200: {
            "description": "작업 진행 상태 스트리밍 성공 - Server-Sent Events로 실시간 진행 상태 제공",
            "content": {
                "text/event-stream": {
                    "examples": {
                        "진행중": {
                            "summary": "분석 진행 중",
                            "value": f"data: {{\"progress\": 0.48, \"message\": \"분석 결과를 생성하고 있습니다...\", \"status\": \"{TaskStatus.IN_PROGRESS}\", \"project_id\": null}}\n\n",
                        },
                        "완료": {
                            "summary": "분석 완료",
                            "value": f"data: {{\"progress\": 1.0, \"message\": \"분석이 완료되었습니다.\", \"status\": \"{TaskStatus.COMPLETED}\", \"project_id\": 2}}\n\n",
                        },
                        "실패": {
                            "summary": "분석 실패",
                            "value": f"data: {{\"progress\": 0.3, \"message\": \"분석 중 오류가 발생했습니다.\", \"status\": \"{TaskStatus.FAILED}\", \"project_id\": null}}\n\n",
                        },
                    }
                }
            },
        },
        401: {"description": "인증 실패 - 클라이언트 호스트 정보를 조회할 수 없는 경우"},
        403: {"description": "접근 권한 없음 - 해당 작업에 대한 접근 권한이 없는 경우 (호스트 불일치 또는 사용자 불일치)"},
        404: {"description": "작업을 찾을 수 없음 - 해당 작업 ID가 존재하지 않는 경우"},
        422: {"description": "검증 오류 - 작업 ID가 유효하지 않은 경우"},
        500: {"description": "서버 내부 오류 - 작업 상태 스트리밍 중 예상치 못한 오류 발생"},
    },
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
    status_code=200,
    response_model=RetrieveOverviewAnalysisUsecaseResponse,
    response_model_exclude_none=True,
    responses={
        200: {"description": "개요 분석 결과 조회 성공 - 상세한 분석 데이터 및 관련 정보 반환"},
        401: {"description": "인증되지 않은 사용자"},
        403: {"description": "접근 권한 없음 - 해당 프로젝트에 대한 권한이 없는 경우"},
        404: {"description": "데이터를 찾을 수 없음 - 개요 분석, 시장 조사, 시장 트렌드, 또는 수익 벤치마크 데이터가 존재하지 않는 경우"},
        422: {"description": "검증 오류 - 프로젝트 ID가 유효하지 않은 경우"},
        500: {"description": "서버 내부 오류 - 저장소 오류 또는 예상치 못한 오류 발생"},
    },
)
async def retrieve_overview_analysis(
    dto: Annotated[RetrieveOverviewAnalysisUsecaseDTO, Depends()],
    usecase: RetrieveOverviewAnalysisUsecase = Depends(get_retrieve_overview_analysis_usecase),
    payload: Payload = Depends(get_current_user),
):
    return await usecase.execute(dto, payload)

@analysis_router.post(
    path="/blocks9",
    status_code=200,
    response_model=Blocks9AnalysisUsecase,
    response_model_exclude_none=True,
    responses={
        200: {"description": "블록 9 분석 결과 반환"},
        422: {"description": "검증 오류 - 입력 데이터가 유효하지 않은 경우"},
        500: {"description": "서버 내부 오류 - 예상치 못한 오류 발생"},
    },
)
async def analyze_blocks9(
    dto: Annotated[Blocks9Input, Body()],
    usecase: Blocks9AnalysisUsecase = Depends(Blocks9AnalysisUsecase()),
    payload: Payload = Depends(get_current_user),
):
    """
    블록 9 분석 실행 엔드포인트
    - 입력 데이터 검증 및 분석 실행
    """
    return await usecase.execute(dto.model_dump(), payload)