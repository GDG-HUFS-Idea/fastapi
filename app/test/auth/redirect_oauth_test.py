import pytest
from unittest import mock

from app.test.mock_config import register_mock_env

register_mock_env()

from fastapi.testclient import TestClient
from fastapi.responses import RedirectResponse

from app.util.enum import OauthProvider
from app.util.exception import (
    OAuthServerException,
    FieldMissingException,
)
from app.service.auth.redirect_oauth import RedirectOAuthService
from app.main import app

client = TestClient(app, raise_server_exceptions=False, follow_redirects=False)


@pytest.mark.asyncio
async def test_redirect_oauth_success():
    """
    성공적으로 OAuth 제공자로 리다이렉트되는 케이스 테스트
    """
    mock_redirect_url = "https://oauth-provider.com/auth"

    async def mock_authorize_redirect(*args, **kwargs):
        return RedirectResponse(url=mock_redirect_url)

    mock_client = mock.MagicMock()
    mock_client.authorize_redirect = mock_authorize_redirect

    with mock.patch(
        "app.core.authlib.oauth.create_client", return_value=mock_client
    ):
        res = client.get(f"/auth/oauth/{OauthProvider.GOOGLE.value}")
        assert res.status_code == 307


@pytest.mark.asyncio
async def test_redirect_oauth_invalid_provider():
    """
    지원하지 않는 OAuth 제공자가 전달된 경우 422 테스트
    """
    res = client.get("/auth/oauth/invalid_provider")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_redirect_oauth_missing_field():
    """
    필수 파라미터가 누락된 경우 400 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise FieldMissingException

    with mock.patch.object(
        RedirectOAuthService, "exec", side_effect=mock_exec
    ):
        res = client.get(f"/auth/oauth/{OauthProvider.GOOGLE.value}")
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_redirect_oauth_server_error():
    """
    OAuth 서버와의 통신 중 오류가 발생한 경우 502 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise OAuthServerException

    with mock.patch.object(
        RedirectOAuthService, "exec", side_effect=mock_exec
    ):
        res = client.get(f"/auth/oauth/{OauthProvider.GOOGLE.value}")
        assert res.status_code == 502


@pytest.mark.asyncio
async def test_redirect_oauth_client_creation_failed():
    """
    OAuth 클라이언트 생성에 실패한 경우 502 테스트
    """

    def mock_create_client(*args, **kwargs):
        raise Exception

    with mock.patch(
        "app.core.authlib.oauth.create_client", side_effect=mock_create_client
    ):
        res = client.get(f"/auth/oauth/{OauthProvider.GOOGLE.value}")
        assert res.status_code == 502
