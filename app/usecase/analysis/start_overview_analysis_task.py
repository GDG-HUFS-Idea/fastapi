import asyncio
from datetime import timedelta
import logging
from typing import Optional
from fastapi import Request
from pydantic import BaseModel

from app.common.enums import TaskStatus
from app.core.cache import get_redis_connection
from app.service.analyzer.overview_analysis import OverviewAnalysisService
from app.service.analyzer.pre_analysis_data import PreAnalysisDataService
from app.service.cache.task_progress import TaskProgress, TaskProgressCache
from app.common.exceptions import UsecaseException, UnauthorizedException, InternalServerException, AnalysisServiceError, CacheError

logger = logging.getLogger(__name__)


class StartOverviewAnalysisTaskUsecaseDTO(BaseModel):
    problem: str
    solution: str


class StartOverviewAnalysisTaskUsecaseResponse(BaseModel):
    task_id: str


class StartOverviewAnalysisTaskUsecase:
    _TASK_EXPIRE_DELTA = timedelta(seconds=600)

    def __init__(
        self,
        pre_analysis_data_service: PreAnalysisDataService,
        overview_analysis_service: OverviewAnalysisService,
        task_progress_cache: TaskProgressCache,
    ) -> None:
        self._pre_analysis_data_service = pre_analysis_data_service
        self._overview_analysis_stream_service = overview_analysis_service
        self._task_progress_cache = task_progress_cache

    async def execute(
        self,
        request: Request,
        dto: StartOverviewAnalysisTaskUsecaseDTO,
    ) -> StartOverviewAnalysisTaskUsecaseResponse:
        try:
            # 1. 클라이언트 호스트 정보 조회 및 작업 시작 시간 기록
            start_time = asyncio.get_event_loop().time()
            host: Optional[str] = getattr(request.client, "host", None)
            if not host:
                raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

            # 2. 작업 진행 상태 캐시에 저장
            task_id = await self._task_progress_cache.set(
                data=TaskProgress(
                    status=TaskStatus.IN_PROGRESS,
                    progress=0.0,
                    message="분석을 시작합니다.",
                    host=host,
                    # user_id= TODO: 나중에 추가
                    start_time=start_time,
                ),
                expire_delta=self._TASK_EXPIRE_DELTA,
            )

            # 3. 백그라운드에서 분석 파이프라인 실행
            asyncio.create_task(self._run_analysis_pipeline(task_id, dto.problem, dto.solution))

            # 4. 즉시 작업 ID 반환
            return StartOverviewAnalysisTaskUsecaseResponse(task_id=task_id)

        except CacheError as exception:
            raise InternalServerException(str(exception)) from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            raise InternalServerException(f"분석 작업 시작 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def _run_analysis_pipeline(
        self,
        task_id: str,
        problem: str,
        solution: str,
    ) -> None:
        try:
            redis = await get_redis_connection()
            self._task_progress_cache = TaskProgressCache(session=redis)

            # 1. 사전 분석 데이터 생성
            pre_analysis_data = await self._pre_analysis_data_service.analyze(task_id, problem, solution)

            # 2. 본 분석 실행
            overview_analysis_data = await self._overview_analysis_stream_service.analyze(task_id, pre_analysis_data)

            # 3. 분석 결과 로깅 (TODO: 추후 저장 로직 추가)
            logger.info(f"분석 완료 - Task ID: {task_id}")

            # 4. 작업 완료 상태 업데이트
            await self._task_progress_cache.update_partial(
                key=task_id,
                status=TaskStatus.COMPLETED,
                progress=1.0,
                message="분석이 완료되었습니다.",
            )

        except AnalysisServiceError as exception:
            logger.error(f"분석 서비스 오류 - Task ID: {task_id}, Error: {str(exception)}")
            try:
                await self._task_progress_cache.update_partial(
                    key=task_id,
                    status=TaskStatus.FAILED,
                    message="분석 처리 중 오류가 발생했습니다.",
                )
            except CacheError:
                pass  # 캐시 업데이트 실패는 무시
        except CacheError as exception:
            logger.error(f"캐시 오류 - Task ID: {task_id}, Error: {str(exception)}")
            # 캐시 오류는 분석 파이프라인을 중단하지 않음
        except Exception as exception:
            logger.error(f"분석 파이프라인 예상치 못한 오류 - Task ID: {task_id}, Error: {str(exception)}")
            try:
                await self._task_progress_cache.update_partial(
                    key=task_id,
                    status=TaskStatus.FAILED,
                    message="분석 중 예상치 못한 오류가 발생했습니다.",
                )
            except CacheError:
                pass  # 캐시 업데이트 실패는 무시
