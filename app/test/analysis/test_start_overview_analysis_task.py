import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.common.exceptions import CacheError
from app.service.auth.jwt import Payload
from app.common import enums
from app.common.enums import TaskStatus
from app.api.endpoint.analysis import analysis_router
from app.usecase.analysis.start_overview_analysis_task import StartOverviewAnalysisTaskUsecase
from app.core.dependency import get_current_user, get_start_overview_analysis_task_usecase


class TestStartOverviewAnalysisTask:
    @pytest.fixture
    def mock_payload(self):
        return Payload(
            id=1,
            name="Test User",
            roles=[enums.UserRole.GENERAL],
        )

    @pytest.fixture
    def mock_services(self):
        pre_analysis_data_service = AsyncMock()
        overview_analysis_service = AsyncMock()
        task_progress_cache = AsyncMock()

        return {
            'pre_analysis_data': pre_analysis_data_service,
            'overview_analysis': overview_analysis_service,
            'task_progress_cache': task_progress_cache,
        }

    @pytest.fixture
    def mock_usecase(self, mock_services):
        usecase = StartOverviewAnalysisTaskUsecase(
            pre_analysis_data_service=mock_services['pre_analysis_data'],
            overview_analysis_service=mock_services['overview_analysis'],
            task_progress_cache=mock_services['task_progress_cache'],
        )

        # _run_analysis_pipeline을 일반 Mock으로 교체
        usecase._run_analysis_pipeline = Mock()

        return usecase

    @pytest.fixture
    def app(self, mock_usecase, mock_payload):
        app = FastAPI()
        app.include_router(analysis_router)

        app.dependency_overrides[get_current_user] = lambda: mock_payload
        app.dependency_overrides[get_start_overview_analysis_task_usecase] = lambda: mock_usecase

        return app

    @pytest.fixture
    def client(self, app):
        with patch('fastapi.Request.client') as mock_client:
            mock_client.host = "127.0.0.1"
            yield TestClient(app)

    @patch('asyncio.create_task')
    def test_start_overview_analysis_task_success(self, mock_create_task, client, mock_services):
        # Given - 200: 개요 분석 작업 시작 성공
        task_id = "uNkpUsM54EZ49CnUjRp_OA"
        mock_services['task_progress_cache'].set.return_value = task_id

        # create_task가 MagicMock 반환
        mock_create_task.return_value = Mock()

        # When
        response = client.post(
            "/analyses/overview",
            json={
                "problem": "자연재해가 빈번하게 발생하는 상황에서 시민들이 필요한 비상용품을 빠르게 구매하기 어려운 문제가 있습니다.",
                "solution": "재해 대비 용품을 전문적으로 판매하는 온라인 플랫폼을 구축하여 시민들이 필요한 물품을 쉽게 구매할 수 있도록 하겠습니다.",
            },
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["task_id"] == task_id
        mock_services['task_progress_cache'].set.assert_called_once()
        mock_create_task.assert_called_once()

    def test_start_overview_analysis_task_unauthorized_no_host(self, client, monkeypatch):
        # Given - 401: 클라이언트 호스트 정보를 조회할 수 없는 경우
        async def mock_execute(request, dto, payload):
            from app.common.exceptions import UnauthorizedException

            raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

        monkeypatch.setattr(client.app.dependency_overrides[get_start_overview_analysis_task_usecase](), "execute", mock_execute)

        # When
        response = client.post(
            "/analyses/overview",
            json={
                "problem": "문제 설명",
                "solution": "솔루션 설명",
            },
        )

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_overview_analysis_task_unauthorized(self):
        # Given - 401: 인증되지 않은 사용자
        app = FastAPI()
        app.include_router(analysis_router)
        client = TestClient(app)

        # When
        response = client.post(
            "/analyses/overview",
            json={
                "problem": "문제 설명",
                "solution": "솔루션 설명",
            },
        )

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_overview_analysis_task_missing_fields(self, client):
        # Given - 422: 필수 필드가 누락된 경우

        # When - problem 누락
        response = client.post(
            "/analyses/overview",
            json={
                "solution": "솔루션 설명",
            },
        )
        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # When - solution 누락
        response = client.post(
            "/analyses/overview",
            json={
                "problem": "문제 설명",
            },
        )
        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # When - 빈 body
        response = client.post("/analyses/overview", json={})
        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_start_overview_analysis_task_cache_error(self, client, mock_services):
        # Given - 500: 캐시 오류 발생
        mock_services['task_progress_cache'].set.side_effect = CacheError("Cache connection failed")

        # When
        response = client.post(
            "/analyses/overview",
            json={
                "problem": "문제 설명",
                "solution": "솔루션 설명",
            },
        )

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
