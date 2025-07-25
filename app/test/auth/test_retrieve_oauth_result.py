import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.common import enums
from app.common.enums import UserRole, SubscriptionPlan
from app.common.exceptions import CacheError, RepositoryError, JWTError
from app.domain.user import User
from app.domain.term import Term
from app.api.endpoint.auth import auth_router
from app.usecase.auth.retrieve_oauth_result import RetrieveOAuthResultUsecase
from app.core.dependency import get_retrieve_oauth_result_usecase
from app.service.cache.oauth_profile import OAuthProfile


class TestRetrieveOAuthResult:
    @pytest.fixture
    def mock_repositories(self):
        user_repo = AsyncMock()
        term_repo = AsyncMock()

        return {
            'user': user_repo,
            'term': term_repo,
        }

    @pytest.fixture
    def mock_oauth_profile_cache(self):
        return AsyncMock()

    @pytest.fixture
    def mock_usecase(self, mock_repositories, mock_oauth_profile_cache):
        return RetrieveOAuthResultUsecase(
            user_repository=mock_repositories['user'],
            term_repository=mock_repositories['term'],
            oauth_profile_cache=mock_oauth_profile_cache,
        )

    @pytest.fixture
    def app(self, mock_usecase):
        app = FastAPI()
        app.include_router(auth_router)

        app.dependency_overrides[get_retrieve_oauth_result_usecase] = lambda: mock_usecase

        return app

    @pytest.fixture
    def client(self, app):
        with patch('fastapi.Request.client') as mock_client:
            mock_client.host = "127.0.0.1"
            yield TestClient(app)

    def test_retrieve_oauth_result_existing_user_success(self, client, mock_repositories, mock_oauth_profile_cache):
        # Given - 200: 기존 사용자는 토큰과 사용자 정보 반환
        oauth_profile = OAuthProfile(name="Test User", email="test@example.com", host="127.0.0.1")
        existing_user = User(
            id=1, name="Test User", email="test@example.com", roles=[UserRole.GENERAL], subscription_plan=SubscriptionPlan.FREE
        )

        mock_oauth_profile_cache.get.return_value = oauth_profile
        mock_repositories['user'].find_by_email.return_value = existing_user
        mock_oauth_profile_cache.evict.return_value = None

        # When
        response = client.get("/auth/oauth/result?code=test_code_123")

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["has_account"] is True
        assert "token" in data
        assert data["user_id"] == 1

    def test_retrieve_oauth_result_new_user_success(self, client, mock_repositories, mock_oauth_profile_cache):
        # Given - 200: 신규 사용자는 임시 코드와 약관 목록 반환
        oauth_profile = OAuthProfile(name="New User", email="new@example.com", host="127.0.0.1")
        active_terms = [
            Term(
                id=1, title="이용약관", content="...", is_required=True, is_active=True, type=enums.TermType.TERMS_OF_SERVICE, version="1.0"
            ),
            Term(
                id=2,
                title="개인정보처리방침",
                content="...",
                is_required=True,
                is_active=True,
                type=enums.TermType.PRIVACY_POLICY,
                version="1.0",
            ),
        ]

        mock_oauth_profile_cache.get.return_value = oauth_profile
        mock_repositories['user'].find_by_email.return_value = None
        mock_repositories['term'].find_active_terms.return_value = active_terms
        mock_oauth_profile_cache.set.return_value = "new_code_456"

        # When
        response = client.get("/auth/oauth/result?code=test_code_123")

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["has_account"] is False
        assert data["code"] == "new_code_456"
        assert data["active_term_ids"] == [1, 2]

    def test_retrieve_oauth_result_unauthorized_no_host(self, client, mock_oauth_profile_cache, monkeypatch):
        # Given - 401: 클라이언트 호스트 정보를 조회할 수 없는 경우
        async def mock_execute(request, dto):
            from app.common.exceptions import UnauthorizedException

            raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

        monkeypatch.setattr(client.app.dependency_overrides[get_retrieve_oauth_result_usecase](), "execute", mock_execute)

        # When
        response = client.get("/auth/oauth/result?code=test_code_123")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_oauth_result_host_mismatch(self, client, mock_oauth_profile_cache):
        # Given - 403: 요청한 호스트와 OAuth 프로필의 호스트가 일치하지 않는 경우
        oauth_profile = OAuthProfile(name="Test User", email="test@example.com", host="192.168.1.1")  # Different host
        mock_oauth_profile_cache.get.return_value = oauth_profile

        # When
        response = client.get("/auth/oauth/result?code=test_code_123")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_oauth_result_not_found_oauth_profile(self, client, mock_oauth_profile_cache):
        # Given - 404: OAuth 프로필을 찾을 수 없는 경우
        mock_oauth_profile_cache.get.return_value = None

        # When
        response = client.get("/auth/oauth/result?code=invalid_code")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_oauth_result_invalid_code(self, client):
        # Given - 422: authorization code가 유효하지 않은 경우

        # When
        response = client.get("/auth/oauth/result?code=short")

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_retrieve_oauth_result_cache_error(self, client, mock_oauth_profile_cache):
        # Given - 500: 캐시 처리 오류
        mock_oauth_profile_cache.get.side_effect = CacheError("Cache connection failed")

        # When
        response = client.get("/auth/oauth/result?code=test_code_123")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
