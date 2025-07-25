import pytest
from unittest.mock import AsyncMock
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.common.exceptions import RepositoryError
from app.api.endpoint.term import term_router
from app.usecase.term.retrieve_terms import RetrieveTermsUsecase
from app.core.dependency import get_retrieve_terms_usecase


class TestRetrieveTerms:
    @pytest.fixture
    def mock_repositories(self):
        term_repo = AsyncMock()
        return {
            'term': term_repo,
        }

    @pytest.fixture
    def mock_usecase(self, mock_repositories):
        return RetrieveTermsUsecase(
            term_repository=mock_repositories['term'],
        )

    @pytest.fixture
    def app(self, mock_usecase):
        app = FastAPI()
        app.include_router(term_router)

        app.dependency_overrides[get_retrieve_terms_usecase] = lambda: mock_usecase

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_retrieve_terms_success_all_found(self, client, mock_repositories):
        # Given - 200: 모든 약관 조회 성공
        from app.domain.term import Term
        from app.common.enums import TermType
        from datetime import datetime

        terms = [
            Term(
                id=1,
                title="서비스 이용약관",
                type=TermType.TERMS_OF_SERVICE,
                version="1.0",
                is_required=True,
                is_active=True,
                content="본 약관은 회사가 제공하는 서비스의 이용 조건을 규정합니다.",
                created_at=datetime(2025, 7, 11, 6, 17, 34, 604304),
            ),
            Term(
                id=2,
                title="개인정보처리방침",
                type=TermType.PRIVACY_POLICY,
                version="1.0",
                is_required=True,
                is_active=True,
                content="회사는 개인정보보호법에 따라 이용자의 개인정보를 보호합니다.",
                created_at=datetime(2025, 7, 11, 6, 17, 34, 604304),
            ),
        ]

        mock_repositories['term'].find_many_by_ids.return_value = terms

        # When
        response = client.get("/terms?ids=1&ids=2")

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["terms"]) == 2
        # missing_ids는 None일 때 response에서 제외됨 (response_model_exclude_none=True)
        assert "missing_ids" not in data
        assert data["terms"][0]["id"] == 1
        assert data["terms"][0]["title"] == "서비스 이용약관"

    def test_retrieve_terms_success_partial_found(self, client, mock_repositories):
        # Given - 200: 일부 약관만 조회 성공 (missing_ids 포함)
        from app.domain.term import Term
        from app.common.enums import TermType
        from datetime import datetime

        terms = [
            Term(
                id=1,
                title="서비스 이용약관",
                type=TermType.TERMS_OF_SERVICE,
                version="1.0",
                is_required=True,
                is_active=True,
                content="본 약관은 회사가 제공하는 서비스의 이용 조건을 규정합니다.",
                created_at=datetime(2025, 7, 11, 6, 17, 34, 604304),
            ),
            Term(
                id=2,
                title="개인정보처리방침",
                type=TermType.PRIVACY_POLICY,
                version="1.0",
                is_required=True,
                is_active=True,
                content="회사는 개인정보보호법에 따라 이용자의 개인정보를 보호합니다.",
                created_at=datetime(2025, 7, 11, 6, 17, 34, 604304),
            ),
        ]

        mock_repositories['term'].find_many_by_ids.return_value = terms

        # When - ID 4는 존재하지 않음
        response = client.get("/terms?ids=1&ids=2&ids=4")

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["terms"]) == 2
        assert data["missing_ids"] == [4]

    def test_retrieve_terms_not_found(self, client, mock_repositories):
        # Given - 404: 요청된 약관을 찾을 수 없는 경우
        mock_repositories['term'].find_many_by_ids.return_value = []

        # When
        response = client.get("/terms?ids=999")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_terms_empty_ids(self, client):
        # Given - 422: 약관 ID 목록이 비어있는 경우

        # When
        response = client.get("/terms?ids=")

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_terms_invalid_ids(self, client):
        # Given - 422: 약관 ID가 유효하지 않은 경우
        invalid_ids = ["abc", "1.5"]

        for invalid_id in invalid_ids:
            # When
            response = client.get(f"/terms?ids={invalid_id}")

            # Then
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_terms_missing_ids_parameter(self, client):
        # Given - 422: ids 파라미터가 누락된 경우

        # When
        response = client.get("/terms")

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_terms_repository_error(self, client, mock_repositories):
        # Given - 500: 데이터베이스 조회 오류 발생
        mock_repositories['term'].find_many_by_ids.side_effect = RepositoryError("Database connection failed")

        # When
        response = client.get("/terms?ids=1&ids=2")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_retrieve_terms_unexpected_error(self, client, mock_repositories):
        # Given - 500: 예상치 못한 오류 발생
        mock_repositories['term'].find_many_by_ids.side_effect = Exception("Unexpected error")

        # When
        response = client.get("/terms?ids=1&ids=2")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
