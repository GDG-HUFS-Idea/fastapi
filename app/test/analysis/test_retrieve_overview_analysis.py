import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.common.exceptions import RepositoryError
from app.service.auth.jwt import Payload
from app.common import enums
from app.api.endpoint.analysis import analysis_router
from app.usecase.analysis.retrieve_overview_analysis import RetrieveOverviewAnalysisUsecase
from app.core.dependency import get_current_user, get_retrieve_overview_analysis_usecase


class TestRetrieveOverviewAnalysis:
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
        overview_repo = AsyncMock()
        market_research_repo = AsyncMock()
        market_trend_repo = AsyncMock()
        revenue_benchmark_repo = AsyncMock()

        return {
            'project': project_repo,
            'overview': overview_repo,
            'market_research': market_research_repo,
            'market_trend': market_trend_repo,
            'revenue_benchmark': revenue_benchmark_repo,
        }

    @pytest.fixture
    def mock_usecase(self, mock_repositories):
        return RetrieveOverviewAnalysisUsecase(
            project_repository=mock_repositories['project'],
            overview_analysis_repository=mock_repositories['overview'],
            market_research_repository=mock_repositories['market_research'],
            market_trend_repository=mock_repositories['market_trend'],
            revenue_benchmark_repository=mock_repositories['revenue_benchmark'],
        )

    @pytest.fixture
    def app(self, mock_usecase, mock_payload):
        app = FastAPI()
        app.include_router(analysis_router)

        app.dependency_overrides[get_current_user] = lambda: mock_payload
        app.dependency_overrides[get_retrieve_overview_analysis_usecase] = lambda: mock_usecase

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_retrieve_overview_analysis_success(self, client, mock_repositories):
        # Given
        from app.common import schemas

        project = Mock(id=1, user_id=1)
        overview_analysis = Mock(
            ksic_hierarchy=schemas.KSICHierarchy(
                large=schemas.KSICItem(code="G", name="도매"),
                medium=schemas.KSICItem(code="G46", name="기타"),
                small=schemas.KSICItem(code="G466", name="전문"),
                detail=schemas.KSICItem(code="G4669", name="기타"),
            ),
            evaluation="test",
            similarity_score=70,
            risk_score=60,
            opportunity_score=75,
            similar_services=[],
            support_programs=[],
            target_markets=[],
            limitations=[],
            marketing_plans=schemas.MarketingPlan(
                approach="test",
                channels=["test"],
                messages=["test"],
                budget=1000,
                kpis=["test"],
                phase=schemas.MarketingPlanPhase(pre="test", launch="test", growth="test"),
            ),
            business_model=schemas.BusinessModel(
                summary="test",
                value_proposition=schemas.BusinessModelValueProposition(main="test", detail="test"),
                revenue_stream="test",
                priorities=[schemas.BusinessModelPriority(name="test", description="test")],
                break_even_point="test",
            ),
            opportunities=[],
            team_requirements=[],
        )

        mock_repositories['overview'].find_by_project_id.return_value = (project, None, overview_analysis)
        mock_repositories['market_research'].find_by_ksic_hierarchy.return_value = Mock(id=1, market_score=80)
        mock_repositories['market_trend'].find_by_market_id.return_value = (
            [Mock(year=2025, size=100, growth_rate=10, currency="KRW", source="test")],
            [],
        )
        mock_repositories['revenue_benchmark'].find_by_market_id.return_value = (
            Mock(average_revenue=100, currency="KRW", source="test"),
            Mock(average_revenue=200, currency="USD", source="test"),
        )

        # When
        response = client.get("/analyses/overview?project_id=1")

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_overview_analysis_unauthorized(self):
        app = FastAPI()
        app.include_router(analysis_router)
        # get_current_user를 오버라이드하지 않음
        client = TestClient(app)

        # When
        response = client.get("/analyses/overview?project_id=1")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_overview_analysis_forbidden(self, client, mock_repositories):
        # Given - 다른 사용자의 프로젝트
        project = Mock(id=1, user_id=2)  # 현재 사용자 ID는 1
        overview_analysis = Mock()

        mock_repositories['overview'].find_by_project_id.return_value = (project, None, overview_analysis)

        # When
        response = client.get("/analyses/overview?project_id=1")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_overview_analysis_not_found_overview(self, client, mock_repositories):
        # Given
        mock_repositories['overview'].find_by_project_id.return_value = None

        # When
        response = client.get("/analyses/overview?project_id=999")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_overview_analysis_not_found_market_research(self, client, mock_repositories):
        # Given
        project = Mock(id=1, user_id=1)
        overview_analysis = Mock(ksic_hierarchy=Mock())

        mock_repositories['overview'].find_by_project_id.return_value = (project, None, overview_analysis)
        mock_repositories['market_research'].find_by_ksic_hierarchy.return_value = None

        # When
        response = client.get("/analyses/overview?project_id=1")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_overview_analysis_not_found_market_trends(self, client, mock_repositories):
        # Given
        project = Mock(id=1, user_id=1)
        overview_analysis = Mock(ksic_hierarchy=Mock())

        mock_repositories['overview'].find_by_project_id.return_value = (project, None, overview_analysis)
        mock_repositories['market_research'].find_by_ksic_hierarchy.return_value = Mock(id=1, market_score=80)
        mock_repositories['market_trend'].find_by_market_id.return_value = None

        # When
        response = client.get("/analyses/overview?project_id=1")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_overview_analysis_not_found_revenue_benchmarks(self, client, mock_repositories):
        # Given
        project = Mock(id=1, user_id=1)
        overview_analysis = Mock(ksic_hierarchy=Mock())

        mock_repositories['overview'].find_by_project_id.return_value = (project, None, overview_analysis)
        mock_repositories['market_research'].find_by_ksic_hierarchy.return_value = Mock(id=1, market_score=80)
        mock_repositories['market_trend'].find_by_market_id.return_value = ([], [])
        mock_repositories['revenue_benchmark'].find_by_market_id.return_value = None

        # When
        response = client.get("/analyses/overview?project_id=1")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_overview_analysis_invalid_project_id(self, client):
        invalid_ids = [0, -1, "abc"]

        for invalid_id in invalid_ids:
            response = client.get(f"/analyses/overview?project_id={invalid_id}")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_overview_analysis_missing_project_id(self, client):
        response = client.get("/analyses/overview")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_overview_analysis_repository_error(self, client, mock_repositories):
        # Given
        mock_repositories['overview'].find_by_project_id.side_effect = RepositoryError("Database connection failed")

        # When
        response = client.get("/analyses/overview?project_id=1")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_retrieve_overview_analysis_unexpected_error(self, client, mock_repositories):
        # Given
        mock_repositories['overview'].find_by_project_id.side_effect = Exception("Unexpected error")

        # When
        response = client.get("/analyses/overview?project_id=1")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
