import pytest
from unittest.mock import AsyncMock
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.common.exceptions import OAuthError
from app.api.endpoint.auth import auth_router
from app.usecase.auth.redirect_oauth import RedirectOAuthUsecase
from app.core.dependency import get_redirect_oauth_usecase


class TestRedirectOAuth:
    @pytest.fixture
    def mock_oauth_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_usecase(self, mock_oauth_service):
        return RedirectOAuthUsecase(
            oauth_service=mock_oauth_service,
        )

    @pytest.fixture
    def app(self, mock_usecase):
        app = FastAPI()
        app.add_middleware(SessionMiddleware, secret_key="test-secret")
        app.include_router(auth_router)

        app.dependency_overrides[get_redirect_oauth_usecase] = lambda: mock_usecase

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_redirect_oauth_success(self, client, mock_oauth_service):
        # Given - 307: OAuth 제공자 인증 페이지로 리다이렉트 성공
        mock_oauth_service.redirect_authorization.return_value = RedirectResponse(
            url="https://accounts.google.com/oauth/authorize?client_id=test"
        )

        # When
        response = client.get("/auth/oauth/google?frontend_redirect_url=http://localhost:3000/auth/callback", follow_redirects=False)

        # Then
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "accounts.google.com" in response.headers["location"]

    def test_redirect_oauth_invalid_provider(self, client):
        # Given - 422: 지원하지 않는 OAuth 제공자

        # When
        response = client.get("/auth/oauth/invalid_provider?frontend_redirect_url=http://localhost:3000/auth/callback")

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_redirect_oauth_invalid_frontend_redirect_url(self, client):
        # Given - 422: frontend_redirect_url이 유효하지 않은 경우

        # When
        response = client.get("/auth/oauth/google?frontend_redirect_url=")

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_redirect_oauth_service_error(self, client, mock_oauth_service):
        # Given - 500: OAuth 서비스 오류
        mock_oauth_service.redirect_authorization.side_effect = OAuthError("OAuth configuration error")

        # When
        response = client.get("/auth/oauth/google?frontend_redirect_url=http://localhost:3000/auth/callback")

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
