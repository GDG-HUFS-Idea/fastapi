import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.common.enums import TermType
from app.common.exceptions import RepositoryError
from app.domain.term import Term
from app.api.endpoint.auth import auth_router
from app.usecase.auth.oauth_sign_up import OAuthSignUpUsecase
from app.core.dependency import get_oauth_sign_up_usecase
from app.service.cache.oauth_profile import OAuthProfile


class TestOAuthSignUp:
    @pytest.fixture
    def mock_repositories(self):
        user_repo = AsyncMock()
        term_repo = AsyncMock()
        user_agreement_repo = AsyncMock()

        return {
            'user': user_repo,
            'term': term_repo,
            'user_agreement': user_agreement_repo,
        }

    @pytest.fixture
    def mock_oauth_profile_cache(self):
        return AsyncMock()

    @pytest.fixture
    def mock_usecase(self, mock_repositories, mock_oauth_profile_cache):
        return OAuthSignUpUsecase(
            user_repository=mock_repositories['user'],
            term_repository=mock_repositories['term'],
            user_agreement_repository=mock_repositories['user_agreement'],
            oauth_profile_cache=mock_oauth_profile_cache,
        )

    @pytest.fixture
    def app(self, mock_usecase):
        app = FastAPI()
        app.include_router(auth_router)

        app.dependency_overrides[get_oauth_sign_up_usecase] = lambda: mock_usecase

        return app

    @pytest.fixture
    def client(self, app):
        with patch('fastapi.Request.client') as mock_client:
            mock_client.host = "127.0.0.1"
            yield TestClient(app)

    def test_oauth_signup_success(self, client, mock_repositories, mock_oauth_profile_cache):
        # Given - 200: OAuth 회원가입 성공 - JWT 토큰과 사용자 정보 반환
        oauth_profile = OAuthProfile(name="New User", email="new@example.com", host="127.0.0.1")
        active_terms = [
            Term(id=1, title="이용약관", content="...", is_required=True, is_active=True, type=TermType.TERMS_OF_SERVICE, version="1.0"),
        ]

        mock_oauth_profile_cache.get.return_value = oauth_profile
        mock_repositories['term'].find_active_terms.return_value = active_terms
        mock_repositories['user'].save.side_effect = lambda user: setattr(user, 'id', 10)

        # When
        response = client.post(
            "/auth/oauth/signup",
            json={
                "code": "test_code_123",
                "term_agreements": [
                    {"term_id": 1, "is_agreed": True},
                ],
            },
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "token" in data
        assert data["user"]["name"] == "New User"

    def test_oauth_signup_unauthorized_no_host(self, client, monkeypatch):
        # Given - 401: 클라이언트 호스트 정보를 조회할 수 없는 경우
        async def mock_execute(request, dto):
            from app.common.exceptions import UnauthorizedException

            raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

        monkeypatch.setattr(client.app.dependency_overrides[get_oauth_sign_up_usecase](), "execute", mock_execute)

        # When
        response = client.post("/auth/oauth/signup", json={"code": "test_code_123", "term_agreements": [{"term_id": 1, "is_agreed": True}]})

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_oauth_signup_host_mismatch(self, client, mock_oauth_profile_cache):
        # Given - 403: 요청한 호스트와 OAuth 프로필의 호스트가 일치하지 않는 경우
        oauth_profile = OAuthProfile(name="New User", email="new@example.com", host="192.168.1.1")  # Different host
        mock_oauth_profile_cache.get.return_value = oauth_profile

        # When
        response = client.post("/auth/oauth/signup", json={"code": "test_code_123", "term_agreements": [{"term_id": 1, "is_agreed": True}]})

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_oauth_signup_not_found_oauth_profile(self, client, mock_oauth_profile_cache):
        # Given - 404: OAuth 프로필을 찾을 수 없는 경우
        mock_oauth_profile_cache.get.return_value = None

        # When
        response = client.post("/auth/oauth/signup", json={"code": "invalid_code", "term_agreements": [{"term_id": 1, "is_agreed": True}]})

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_oauth_signup_invalid_term_id(self, client, mock_repositories, mock_oauth_profile_cache):
        # Given - 422: 유효하지 않은 약관 ID
        oauth_profile = OAuthProfile(name="New User", email="new@example.com", host="127.0.0.1")
        active_terms = [
            Term(id=1, title="이용약관", content="...", is_required=True, is_active=True, type=TermType.TERMS_OF_SERVICE, version="1.0"),
        ]

        mock_oauth_profile_cache.get.return_value = oauth_profile
        mock_repositories['term'].find_active_terms.return_value = active_terms

        # When
        response = client.post(
            "/auth/oauth/signup",
            json={
                "code": "test_code_123",
                "term_agreements": [
                    {"term_id": 1, "is_agreed": True},
                    {"term_id": 99, "is_agreed": True},  # Invalid
                ],
            },
        )

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_oauth_signup_invalid_code(self, client):
        # Given - 422: 요청 데이터 형식이 유효하지 않은 경우

        # When
        response = client.post(
            "/auth/oauth/signup", json={"code": "short", "term_agreements": [{"term_id": 1, "is_agreed": True}]}  # Too short
        )

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_oauth_signup_repository_error(self, client, mock_repositories, mock_oauth_profile_cache):
        # Given - 500: 저장소 처리 오류
        oauth_profile = OAuthProfile(name="New User", email="new@example.com", host="127.0.0.1")
        active_terms = [
            Term(id=1, title="이용약관", content="...", is_required=True, is_active=True, type=TermType.TERMS_OF_SERVICE, version="1.0"),
        ]

        mock_oauth_profile_cache.get.return_value = oauth_profile
        mock_repositories['term'].find_active_terms.return_value = active_terms
        mock_repositories['user'].save.side_effect = RepositoryError("Database connection failed")

        # When
        response = client.post("/auth/oauth/signup", json={"code": "test_code_123", "term_agreements": [{"term_id": 1, "is_agreed": True}]})

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
