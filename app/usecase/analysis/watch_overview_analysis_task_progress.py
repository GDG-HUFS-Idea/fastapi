import asyncio
import json
from typing import AsyncGenerator, Optional
from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.common.enums import TaskStatus
from app.service.cache.task_progress import TaskProgressCache
from app.common.exceptions import UsecaseException, UnauthorizedException, InternalServerException, CacheError


class WatchOverviewAnalysisTaskProgressUsecaseDTO(BaseModel):
    task_id: str


class WatchOverviewAnalysisTaskProgressUsecase:
    _TIMEOUT_SECONDS = 600
    _POLLING_INTERVAL = 5

    def __init__(self, task_progress_cache: TaskProgressCache) -> None:
        self._task_progress_cache = task_progress_cache

    async def execute(
        self,
        request: Request,
        dto: WatchOverviewAnalysisTaskProgressUsecaseDTO,
    ) -> StreamingResponse:
        try:
            # 1. 클라이언트 호스트 정보 조회
            host: Optional[str] = getattr(request.client, "host", None)
            if not host:
                raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

            # 2. 스트리밍 응답 생성
            return StreamingResponse(
                self._operation(dto, host),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control",
                },
            )

        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            raise InternalServerException(f"작업 상태 스트리밍 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def _operation(
        self,
        dto: WatchOverviewAnalysisTaskProgressUsecaseDTO,
        host: str,
    ) -> AsyncGenerator[str, None]:
        try:
            start_time = asyncio.get_event_loop().time()

            while True:
                # 타임아웃 체크
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > self._TIMEOUT_SECONDS:
                    yield f"data: {json.dumps({'error': '작업 진행 상태 조회가 타임아웃되었습니다.'})}\n\n"
                    break

                # 작업 진행 상태 조회
                task_progress = await self._task_progress_cache.get(dto.task_id)

                if not task_progress:
                    yield f"data: {json.dumps({'error': '해당 작업을 찾을 수 없습니다.'})}\n\n"
                    break

                if host != task_progress.host:
                    yield f"data: {json.dumps({'error': '해당 작업에 대한 접근 권한이 없습니다.'})}\n\n"
                    break

                # 작업 진행 상태 응답
                response_data = {
                    "progress": task_progress.progress,
                    "message": task_progress.message,
                    "status": task_progress.status,
                }
                yield f"data: {json.dumps(response_data)}\n\n"

                # 작업이 완료되었거나 실패한 경우 종료
                if task_progress.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    break

                # 일정 시간 대기 후 다시 조회
                await asyncio.sleep(self._POLLING_INTERVAL)

        except CacheError as exception:
            yield f"data: {json.dumps({'error': {str(exception)}})}\n\n"
        except Exception as exception:
            yield f"data: {json.dumps({'error': f'작업 상태 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}'})}\n\n"
