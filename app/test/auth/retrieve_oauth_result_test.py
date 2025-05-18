import pytest
from unittest import mock

from app.test.mock_config import register_mock_env

register_mock_env()

from fastapi.testclient import TestClient

from app.util.enum import UserRole
from app.util.exception import (
    CacheServerException,
    DBServerException,
    FieldMissingException,
    NoPermissionException,
    DataNotFoundException,
)
from app.service.auth.retrieve_oauth_result import RetrieveOAuthResultService
from app.main import app

client = TestClient(app, raise_server_exceptions=False, follow_redirects=False)


@pytest.mark.asyncio
async def test_retrieve_oauth_result_existing_user_success():
    """
    이미 계정이 있는 사용자의 OAuth 결과 조회 성공 테스트 (200)
    """
    mock_response = {
        "has_account": True,
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_id": 123,
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
        RetrieveOAuthResultService, "exec", side_effect=mock_exec
    ):
        res = client.get("/auth/oauth/result?code=FYVjdmoq9RQ2UPYu_cCRhA")
        assert res.status_code == 200
        data = res.json()
        assert data["has_account"] == True
        assert "token" in data
        assert "user_id" in data
        assert "roles" in data
        assert "name" in data


@pytest.mark.asyncio
async def test_retrieve_oauth_result_new_user_success():
    """
    계정이 없는 신규 사용자의 OAuth 결과 조회 성공 테스트 (200)
    """
    mock_response = {
        "has_account": False,
        "code": "FYVjdmoq9RQ2UPYu_cCRhA",
        "signup_term_ids": [1, 2, 3],
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
        RetrieveOAuthResultService, "exec", side_effect=mock_exec
    ):
        res = client.get("/auth/oauth/result?code=FYVjdmoq9RQ2UPYu_cCRhA")
        assert res.status_code == 200
        data = res.json()
        assert data["has_account"] == False
        assert "code" in data
        assert "signup_term_ids" in data


@pytest.mark.asyncio
async def test_retrieve_oauth_result_field_missing():
    """
    필수 파라미터가 누락된 경우 400 테스트
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
        RetrieveOAuthResultService, "exec", side_effect=mock_exec
    ):
        res = client.get("/auth/oauth/result")
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_retrieve_oauth_result_no_permission():
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
        RetrieveOAuthResultService, "exec", side_effect=mock_exec
    ):
        res = client.get("/auth/oauth/result?code=FYVjdmoq9RQ2UPYu_cCRhA")
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_retrieve_oauth_result_data_not_found():
    """
    OAuth 프로필을 찾을 수 없거나 필요한 약관 정보가 존재하지 않는 경우 404 테스트
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
        RetrieveOAuthResultService, "exec", side_effect=mock_exec
    ):
        res = client.get("/auth/oauth/result?code=FYVjdmoq9RQ2UPYu_cCRhA")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_retrieve_oauth_result_validation_error():
    """
    요청 데이터의 형식이 올바르지만 비즈니스 규칙에 따른 유효성 검증에 실패한 경우 422 테스트
    """
    res = client.get("/auth/oauth/result?code=invalid")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_retrieve_oauth_result_cache_server_error():
    """
    Redis 캐시 서버와의 통신 중 오류가 발생한 경우 502 테스트
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
        RetrieveOAuthResultService, "exec", side_effect=mock_exec
    ):
        res = client.get("/auth/oauth/result?code=FYVjdmoq9RQ2UPYu_cCRhA")
        assert res.status_code == 502


@pytest.mark.asyncio
async def test_retrieve_oauth_result_db_server_error():
    """
    데이터베이스 서버와의 통신 중 오류가 발생한 경우 502 테스트
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
        RetrieveOAuthResultService, "exec", side_effect=mock_exec
    ):
        res = client.get("/auth/oauth/result?code=FYVjdmoq9RQ2UPYu_cCRhA")
        assert res.status_code == 502


@pytest.mark.asyncio
async def test_retrieve_oauth_result_internal_server_error():
    """
    원인 불명의 내부 로직 오류가 발생한 경우 500 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise Exception("예상치 못한 오류")

    mock_pg_session = mock.MagicMock()
    mock_redis_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch(
        "app.api.dep.get_redis_session",
        return_value=mock_redis_session,
    ), mock.patch.object(
        RetrieveOAuthResultService, "exec", side_effect=mock_exec
    ):
        res = client.get("/auth/oauth/result?code=FYVjdmoq9RQ2UPYu_cCRhA")
        assert res.status_code == 500
