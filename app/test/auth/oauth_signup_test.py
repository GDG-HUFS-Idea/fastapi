import pytest
from unittest import mock

from app.test.mock_config import register_mock_env

register_mock_env()

from fastapi.testclient import TestClient

from app.main import app
from app.util.enum import UserRole
from app.util.exception import (
    FieldMissingException,
    ValidationException,
    NoPermissionException,
    DataNotFoundException,
    DBServerException,
    CacheServerException,
)
from app.service.auth.oauth_signup import OAuthSignUpService

client = TestClient(app, raise_server_exceptions=False)


@pytest.mark.asyncio
async def test_oauth_signup_success():
    """
    OAuth 회원가입이 성공적으로 처리되는 케이스 테스트
    """
    mock_response = {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_id": 2,
        "roles": [UserRole.GENERAL],
        "name": "홍길동",
    }

    async def mock_exec(*args, **kwargs):
        return mock_response

    mock_pg_session = mock.MagicMock()
    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        OAuthSignUpService, "exec", side_effect=mock_exec
    ):
        res = client.post(
            "/auth/oauth/signup",
            json={
                "code": "FYVjdmoq9RQ2UPYu_cCRhA",
                "term_agreements": [
                    {"term_id": 1, "has_agreed": True},
                    {"term_id": 2, "has_agreed": True},
                    {"term_id": 3, "has_agreed": False},
                ],
            },
        )
        assert res.status_code == 201
        assert res.json() == mock_response


@pytest.mark.asyncio
async def test_oauth_signup_field_missing():
    """
    필수 필드가 누락된 경우 400 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise FieldMissingException

    mock_pg_session = mock.MagicMock()
    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        OAuthSignUpService, "exec", side_effect=mock_exec
    ):
        res = client.post(
            "/auth/oauth/signup",
            json={
                "code": "FYVjdmoq9RQ2UPYu_cCRhA",
            },
        )
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_oauth_signup_validation_error():
    """
    제출된 약관 동의 정보가 유효하지 않은 경우 422 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise ValidationException

    mock_pg_session = mock.MagicMock()
    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        OAuthSignUpService, "exec", side_effect=mock_exec
    ):
        res = client.post(
            "/auth/oauth/signup",
            json={
                "code": "FYVjdmoq9RQ2UPYu_cCRhA",
                "term_agreements": [
                    {"term_id": 1, "has_agreed": True},
                    {
                        "term_id": 99,
                        "has_agreed": True,
                    },  # 존재하지 않는 약관 ID
                ],
            },
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_oauth_signup_no_permission():
    """
    요청 호스트와 OAuth 프로필의 호스트가 일치하지 않는 경우 403 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise NoPermissionException

    mock_pg_session = mock.MagicMock()
    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        OAuthSignUpService, "exec", side_effect=mock_exec
    ):
        res = client.post(
            "/auth/oauth/signup",
            json={
                "code": "FYVjdmoq9RQ2UPYu_cCRhA",
                "term_agreements": [
                    {"term_id": 1, "has_agreed": True},
                    {"term_id": 2, "has_agreed": True},
                ],
            },
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_oauth_signup_data_not_found():
    """
    OAuth 인증 코드에 해당하는 프로필 정보 또는 약관 정보를 찾을 수 없는 경우 404 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise DataNotFoundException

    mock_pg_session = mock.MagicMock()
    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        OAuthSignUpService, "exec", side_effect=mock_exec
    ):
        res = client.post(
            "/auth/oauth/signup",
            json={
                "code": "invalid_code",
                "term_agreements": [
                    {"term_id": 1, "has_agreed": True},
                    {"term_id": 2, "has_agreed": True},
                ],
            },
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_oauth_signup_db_server_error():
    """
    DB 서버 오류가 발생한 경우 502 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise DBServerException

    mock_pg_session = mock.MagicMock()
    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        OAuthSignUpService, "exec", side_effect=mock_exec
    ):
        res = client.post(
            "/auth/oauth/signup",
            json={
                "code": "FYVjdmoq9RQ2UPYu_cCRhA",
                "term_agreements": [
                    {"term_id": 1, "has_agreed": True},
                    {"term_id": 2, "has_agreed": True},
                ],
            },
        )
        assert res.status_code == 502


@pytest.mark.asyncio
async def test_oauth_signup_cache_server_error():
    """
    캐시 서버 오류가 발생한 경우 502 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise CacheServerException

    mock_pg_session = mock.MagicMock()
    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        OAuthSignUpService, "exec", side_effect=mock_exec
    ):
        res = client.post(
            "/auth/oauth/signup",
            json={
                "code": "FYVjdmoq9RQ2UPYu_cCRhA",
                "term_agreements": [
                    {"term_id": 1, "has_agreed": True},
                    {"term_id": 2, "has_agreed": True},
                ],
            },
        )
        assert res.status_code == 502
