import pytest
import json
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.common.exceptions import CacheError
from app.service.auth.jwt import Payload
from app.common import enums
from app.common.enums import TaskStatus
from app.api.endpoint.analysis import analysis_router
from app.usecase.analysis.watch_overview_analysis_task_progress import WatchOverviewAnalysisTaskProgressUsecase
from app.core.dependency import get_current_user, get_watch_overview_analysis_task_progress_usecase
from app.service.cache.task_progress import TaskProgress


class TestWatchOverviewAnalysisTaskProgress:
    @pytest.fixture
    def mock_payload(self):
        return Payload(
            id=1,
            name="Test User",
            roles=[enums.UserRole.GENERAL],
        )

    @pytest.fixture
    def mock_task_progress_cache(self):
        return AsyncMock()

    @pytest.fixture
    def mock_usecase(self, mock_task_progress_cache):
        return WatchOverviewAnalysisTaskProgressUsecase(
            task_progress_cache=mock_task_progress_cache,
        )

    @pytest.fixture
    def app(self, mock_usecase, mock_payload):
        app = FastAPI()
        app.include_router(analysis_router)

        app.dependency_overrides[get_current_user] = lambda: mock_payload
        app.dependency_overrides[get_watch_overview_analysis_task_progress_usecase] = lambda: mock_usecase

        return app

    @pytest.fixture
    def client(self, app):
        with patch('fastapi.Request.client') as mock_client:
            mock_client.host = "127.0.0.1"
            yield TestClient(app)

    def test_watch_overview_analysis_task_progress_success_in_progress(self, client, mock_task_progress_cache):
        # Given - 200: 진행 중인 작업 상태 스트리밍
        task_progress = TaskProgress(
            status=TaskStatus.IN_PROGRESS,
            progress=0.48,
            message="분석 결과를 생성하고 있습니다...",
            host="127.0.0.1",
            user_id=1,
            start_time=0.0,
            project_id=None,
        )

        # 첫 번째 호출은 권한 확인용, 두 번째 호출은 스트리밍용 (진행 중 -> 완료)
        mock_task_progress_cache.get.side_effect = [
            task_progress,  # 권한 확인
            task_progress,  # 첫 번째 폴링
            TaskProgress(  # 두 번째 폴링 - 완료 상태
                status=TaskStatus.COMPLETED,
                progress=1.0,
                message="분석이 완료되었습니다.",
                host="127.0.0.1",
                user_id=1,
                start_time=0.0,
                project_id=2,
            ),
        ]

        # When
        with client.stream("GET", "/analyses/overview/progress?task_id=test_task_123") as response:
            # Then
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # 스트리밍 데이터 읽기
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])  # "data: " 제거
                    events.append(event_data)

            # 최소 2개의 이벤트가 있어야 함 (진행 중, 완료)
            assert len(events) >= 2
            assert events[0]["status"] == TaskStatus.IN_PROGRESS
            assert events[-1]["status"] == TaskStatus.COMPLETED
            assert events[-1]["project_id"] == 2

    def test_watch_overview_analysis_task_progress_success_completed(self, client, mock_task_progress_cache):
        # Given - 200: 이미 완료된 작업
        task_progress = TaskProgress(
            status=TaskStatus.COMPLETED,
            progress=1.0,
            message="분석이 완료되었습니다.",
            host="127.0.0.1",
            user_id=1,
            start_time=0.0,
            project_id=2,
        )

        mock_task_progress_cache.get.return_value = task_progress

        # When
        with client.stream("GET", "/analyses/overview/progress?task_id=test_task_123") as response:
            # Then
            assert response.status_code == status.HTTP_200_OK

            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)

            assert len(events) == 1
            assert events[0]["status"] == TaskStatus.COMPLETED
            assert events[0]["project_id"] == 2

    def test_watch_overview_analysis_task_progress_success_failed(self, client, mock_task_progress_cache):
        # Given - 200: 실패한 작업
        task_progress = TaskProgress(
            status=TaskStatus.FAILED,
            progress=0.3,
            message="분석 중 오류가 발생했습니다.",
            host="127.0.0.1",
            user_id=1,
            start_time=0.0,
            project_id=None,
        )

        mock_task_progress_cache.get.return_value = task_progress

        # When
        with client.stream("GET", "/analyses/overview/progress?task_id=test_task_123") as response:
            # Then
            assert response.status_code == status.HTTP_200_OK

            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)

            assert len(events) == 1
            assert events[0]["status"] == TaskStatus.FAILED
            assert events[0]["project_id"] is None

    def test_watch_overview_analysis_task_progress_unauthorized_no_host(self, client, monkeypatch):
        # Given - 401: 클라이언트 호스트 정보를 조회할 수 없는 경우
        async def mock_execute(request, dto, payload):
            from app.common.exceptions import UnauthorizedException

            raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

        monkeypatch.setattr(client.app.dependency_overrides[get_watch_overview_analysis_task_progress_usecase](), "execute", mock_execute)

        # When
        response = client.get("/analyses/overview/progress?task_id=test_task_123")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_watch_overview_analysis_task_progress_unauthorized(self):
        # Given - 401: 인증되지 않은 사용자
        app = FastAPI()
        app.include_router(analysis_router)
        client = TestClient(app)

        # When
        response = client.get("/analyses/overview/progress?task_id=test_task_123")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_watch_overview_analysis_task_progress_forbidden_host_mismatch(self, client, mock_task_progress_cache):
        # Given - 403: 호스트 불일치
        task_progress = TaskProgress(
            status=TaskStatus.IN_PROGRESS,
            progress=0.5,
            message="진행 중",
            host="192.168.1.1",  # 다른 호스트
            user_id=1,
            start_time=0.0,
        )

        mock_task_progress_cache.get.return_value = task_progress

        # When
        response = client.get("/analyses/overview/progress?task_id=test_task_123")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_watch_overview_analysis_task_progress_forbidden_user_mismatch(self, client, mock_task_progress_cache):
        # Given - 403: 사용자 불일치
        task_progress = TaskProgress(
            status=TaskStatus.IN_PROGRESS,
            progress=0.5,
            message="진행 중",
            host="127.0.0.1",
            user_id=999,  # 다른 사용자
            start_time=0.0,
        )

        mock_task_progress_cache.get.return_value = task_progress

        # When
        response = client.get("/analyses/overview/progress?task_id=test_task_123")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_watch_overview_analysis_task_progress_not_found(self, client, mock_task_progress_cache):
        # Given - 404: 작업을 찾을 수 없음
        mock_task_progress_cache.get.return_value = None

        # When
        response = client.get("/analyses/overview/progress?task_id=invalid_task_id")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_watch_overview_analysis_task_progress_invalid_task_id(self, client):
        # Given - 422: 유효하지 않은 작업 ID

        # When - 빈 task_id
        response = client.get("/analyses/overview/progress?task_id=")

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_watch_overview_analysis_task_progress_missing_task_id(self, client):
        # Given - 422: task_id 파라미터 누락

        # When
        response = client.get("/analyses/overview/progress")

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_watch_overview_analysis_task_progress_unexpected_error(self, client, mock_task_progress_cache):
        # Given - 500: 예상치 못한 오류
        mock_task_progress_cache.get.side_effect = Exception("Unexpected error")

        # When
        response = client.get("/analyses/overview/progress?task_id=test_task_123")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch('asyncio.sleep', new_callable=AsyncMock)
    def test_watch_overview_analysis_task_progress_timeout(self, mock_sleep, client, mock_task_progress_cache, monkeypatch):
        # Given - 200: 타임아웃 시나리오
        task_progress = TaskProgress(
            status=TaskStatus.IN_PROGRESS,
            progress=0.5,
            message="진행 중",
            host="127.0.0.1",
            user_id=1,
            start_time=0.0,
        )

        mock_task_progress_cache.get.return_value = task_progress

        # 타임아웃을 빠르게 발생시키기 위해 _TIMEOUT_SECONDS를 짧게 설정
        monkeypatch.setattr(client.app.dependency_overrides[get_watch_overview_analysis_task_progress_usecase](), "_TIMEOUT_SECONDS", 0.1)

        # When
        with client.stream("GET", "/analyses/overview/progress?task_id=test_task_123") as response:
            # Then
            assert response.status_code == status.HTTP_200_OK

            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)

            # 타임아웃 에러 메시지 확인
            assert any("타임아웃" in str(event.get("error", "")) for event in events)

    def test_watch_overview_analysis_task_progress_cache_error_during_stream(self, client, mock_task_progress_cache):
        # Given - 200: 스트리밍 중 캐시 오류 발생
        task_progress = TaskProgress(
            status=TaskStatus.IN_PROGRESS,
            progress=0.5,
            message="진행 중",
            host="127.0.0.1",
            user_id=1,
            start_time=0.0,
        )

        # 첫 번째 호출은 성공, 두 번째 호출에서 캐시 오류
        mock_task_progress_cache.get.side_effect = [
            task_progress,  # 권한 확인용
            CacheError("Cache connection lost"),  # 스트리밍 중 오류
        ]

        # When
        with client.stream("GET", "/analyses/overview/progress?task_id=test_task_123") as response:
            # Then
            assert response.status_code == status.HTTP_200_OK

            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)

            # 캐시 오류 메시지 확인
            assert any("Cache connection lost" in str(event.get("error", "")) for event in events)
