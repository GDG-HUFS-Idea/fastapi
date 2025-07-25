import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.common.exceptions import RepositoryError
from app.service.auth.jwt import Payload
from app.common import enums
from app.api.endpoint.project import project_router
from app.usecase.project.retrieve_my_projects import RetrieveMyProjectsUsecase
from app.core.dependency import get_current_user, get_retrieve_my_projects_usecase


class TestRetrieveMyProjects:
    @pytest.fixture
    def mock_payload(self):
        return Payload(
            id=1,
            name="Test User",
            roles=[enums.UserRole.GENERAL],
        )

    @pytest.fixture
    def mock_repositories(self):
        project_repo = AsyncMock()
        return {
            'project': project_repo,
        }

    @pytest.fixture
    def mock_usecase(self, mock_repositories):
        return RetrieveMyProjectsUsecase(
            project_repository=mock_repositories['project'],
        )

    @pytest.fixture
    def app(self, mock_usecase, mock_payload):
        app = FastAPI()
        app.include_router(project_router)

        app.dependency_overrides[get_current_user] = lambda: mock_payload
        app.dependency_overrides[get_retrieve_my_projects_usecase] = lambda: mock_usecase

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_retrieve_my_projects_success(self, client, mock_repositories):
        # Given - 200: 프로젝트 목록 조회 성공
        from app.domain.project import Project
        from app.common.enums import ProjectStatus
        from datetime import datetime

        projects = [
            Project(
                id=1,
                user_id=1,
                name="자연재해 대비 물품 판매",
                status=ProjectStatus.ANALYZED,
                created_at=datetime(2025, 7, 11, 6, 19, 5, 851264),
                updated_at=datetime(2025, 7, 11, 6, 20, 38, 318675),
            ),
            Project(
                id=2,
                user_id=1,
                name="온라인 교육 플랫폼",
                status=ProjectStatus.IN_PROGRESS,
                created_at=datetime(2025, 7, 10, 15, 30, 22, 123456),
                updated_at=datetime(2025, 7, 11, 9, 45, 15, 987654),
            ),
        ]

        mock_repositories['project'].find_many_by_user_id.return_value = projects

        # When
        response = client.get("/projects?offset=0&limit=50")

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["projects"]) == 2
        assert data["projects"][0]["id"] == 1
        assert data["projects"][0]["name"] == "자연재해 대비 물품 판매"
        assert data["projects"][0]["status"] == "analyzed"

    def test_retrieve_my_projects_unauthorized(self):
        # Given - 401: 인증되지 않은 사용자
        app = FastAPI()
        app.include_router(project_router)
        # get_current_user를 오버라이드하지 않음
        client = TestClient(app)

        # When
        response = client.get("/projects?offset=0&limit=50")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_my_projects_not_found(self, client, mock_repositories):
        # Given - 404: 해당 사용자의 프로젝트가 존재하지 않는 경우
        mock_repositories['project'].find_many_by_user_id.return_value = []

        # When
        response = client.get("/projects?offset=0&limit=50")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_my_projects_invalid_offset(self, client):
        # Given - 422: offset 파라미터가 유효하지 않은 경우
        invalid_offsets = [-1, "abc"]

        for invalid_offset in invalid_offsets:
            # When
            response = client.get(f"/projects?offset={invalid_offset}&limit=50")

            # Then
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_my_projects_invalid_limit(self, client):
        # Given - 422: limit 파라미터가 유효하지 않은 경우
        invalid_limits = [0, 101, -1, "abc"]

        for invalid_limit in invalid_limits:
            # When
            response = client.get(f"/projects?offset=0&limit={invalid_limit}")

            # Then
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_my_projects_missing_parameters(self, client):
        # Given - 422: 필수 파라미터가 누락된 경우

        # When - offset 누락
        response = client.get("/projects?limit=50")
        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # When - limit 누락
        response = client.get("/projects?offset=0")
        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # When - 모든 파라미터 누락
        response = client.get("/projects")
        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_my_projects_repository_error(self, client, mock_repositories):
        # Given - 500: 저장소 오류 발생
        mock_repositories['project'].find_many_by_user_id.side_effect = RepositoryError("Database connection failed")

        # When
        response = client.get("/projects?offset=0&limit=50")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_retrieve_my_projects_unexpected_error(self, client, mock_repositories):
        # Given - 500: 예상치 못한 오류 발생
        mock_repositories['project'].find_many_by_user_id.side_effect = Exception("Unexpected error")

        # When
        response = client.get("/projects?offset=0&limit=50")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
