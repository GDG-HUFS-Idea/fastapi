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
    CSRFException,
    CacheServerException,
)
from app.service.auth.handle_oauth_callback import HandleOAuthCallbackService
from app.main import app

client = TestClient(app, raise_server_exceptions=False, follow_redirects=False)


@pytest.mark.asyncio
async def test_handle_oauth_callback_success():
    """
    OAuth 콜백이 성공적으로 처리되고 리다이렉트되는 케이스 테스트
    """
    mock_frontend_url = "https://frontend.com/auth?token=mock_token"

    async def mock_exec(*args, **kwargs):
        return RedirectResponse(url=mock_frontend_url, status_code=307)

    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        HandleOAuthCallbackService, "exec", side_effect=mock_exec
    ):
        res = client.get(
            f"/auth/oauth/{OauthProvider.GOOGLE.value}/callback?code=mock_code&state=mock_state"
        )
        assert res.status_code == 307
        assert res.headers["location"] == mock_frontend_url


@pytest.mark.asyncio
async def test_handle_oauth_callback_field_missing():
    """
    필수 파라미터가 누락된 경우 400 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise FieldMissingException

    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        HandleOAuthCallbackService, "exec", side_effect=mock_exec
    ):
        res = client.get(f"/auth/oauth/{OauthProvider.GOOGLE.value}/callback")
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_handle_oauth_callback_csrf_exception():
    """
    CSRF 공격 가능성이 감지된 경우 403 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise CSRFException

    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        HandleOAuthCallbackService, "exec", side_effect=mock_exec
    ):
        res = client.get(
            f"/auth/oauth/{OauthProvider.GOOGLE.value}/callback?code=mock_code&state=invalid_state"
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_handle_oauth_callback_invalid_provider():
    """
    지원하지 않는 OAuth 제공자가 전달된 경우 422 테스트
    """

    res = client.get(
        "/auth/oauth/invalid_provider/callback?code=mock_code&state=mock_state"
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_handle_oauth_callback_oauth_server_error():
    """
    OAuth 서버와의 통신 중 오류가 발생한 경우 502 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise OAuthServerException

    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        HandleOAuthCallbackService, "exec", side_effect=mock_exec
    ):
        res = client.get(
            f"/auth/oauth/{OauthProvider.GOOGLE.value}/callback?code=mock_code&state=mock_state"
        )
        assert res.status_code == 502


@pytest.mark.asyncio
async def test_handle_oauth_callback_cache_server_error():
    """
    캐시 서버와의 통신 중 오류가 발생한 경우 502 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise CacheServerException

    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        HandleOAuthCallbackService, "exec", side_effect=mock_exec
    ):
        res = client.get(
            f"/auth/oauth/{OauthProvider.GOOGLE.value}/callback?code=mock_code&state=mock_state"
        )
        assert res.status_code == 502
