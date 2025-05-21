import pytest
from unittest import mock
from datetime import datetime

from app.test.mock_config import register_mock_env

register_mock_env()

from fastapi.testclient import TestClient

from app.util.enum import TermType
from app.util.exception import (
    DBServerException,
    FieldMissingException,
    DataNotFoundException,
)
from app.service.term.retrieve_terms import (
    RetrieveTermsService,
    RetrieveTermsServiceResponse,
    TermResponse,
)
from app.main import app

client = TestClient(app, raise_server_exceptions=False, follow_redirects=False)


@pytest.mark.asyncio
async def test_retrieve_terms_success():
    """
    약관 정보 조회 성공 테스트
    """
    mock_terms = [
        TermResponse(
            id=1,
            title="서비스 이용약관",
            type=TermType.TERMS_OF_SERVICE,
            content="본 약관은 서비스 이용에 관한 약관입니다...",
            is_required=True,
            created_at=datetime.fromisoformat("2024-05-01T09:30:00.000Z"),
            updated_at=datetime.fromisoformat("2024-05-01T09:30:00.000Z"),
        ),
        TermResponse(
            id=2,
            title="개인정보 처리방침",
            type=TermType.PRIVACY_POLICY,
            content="개인정보 처리방침 내용입니다...",
            is_required=True,
            created_at=datetime.fromisoformat("2024-05-01T09:35:00.000Z"),
            updated_at=datetime.fromisoformat("2024-05-01T09:35:00.000Z"),
        ),
    ]

    mock_response = RetrieveTermsServiceResponse(terms=mock_terms)

    async def mock_exec(*args, **kwargs):
        return mock_response

    mock_pg_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch.object(RetrieveTermsService, "exec", side_effect=mock_exec):
        res = client.get("/terms?ids=1&ids=2")
        assert res.status_code == 200
        data = res.json()
        assert "terms" in data
        assert len(data["terms"]) == 2
        assert data["terms"][0]["id"] == 1
        assert data["terms"][1]["id"] == 2
        assert data["terms"][0]["title"] == "서비스 이용약관"
        assert data["terms"][1]["title"] == "개인정보 처리방침"
        assert "missing_ids" not in data


@pytest.mark.asyncio
async def test_retrieve_terms_partial_success():
    """
    일부 약관 ID 누락된 부분 성공 테스트
    """
    mock_terms = [
        TermResponse(
            id=1,
            title="서비스 이용약관",
            type=TermType.TERMS_OF_SERVICE,
            content="본 약관은 서비스 이용에 관한 약관입니다...",
            is_required=True,
            created_at=datetime.fromisoformat("2024-05-01T09:30:00.000Z"),
            updated_at=datetime.fromisoformat("2024-05-01T09:30:00.000Z"),
        )
    ]

    mock_response = RetrieveTermsServiceResponse(
        terms=mock_terms, missing_ids=[2, 3]
    )

    async def mock_exec(*args, **kwargs):
        return mock_response

    mock_pg_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch.object(RetrieveTermsService, "exec", side_effect=mock_exec):
        res = client.get("/terms?ids=1&ids=2&ids=3")
        assert res.status_code == 200
        data = res.json()
        assert "terms" in data
        assert "missing_ids" in data
        assert len(data["terms"]) == 1
        assert data["terms"][0]["id"] == 1
        assert data["missing_ids"] == [2, 3]


@pytest.mark.asyncio
async def test_retrieve_terms_field_missing():
    """
    필수 쿼리 파라미터(ids)가 누락된 경우 400 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise FieldMissingException

    mock_pg_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch.object(RetrieveTermsService, "exec", side_effect=mock_exec):
        res = client.get("/terms")
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_retrieve_terms_validation_error():
    """
    요청된 term ID 목록의 형식이 유효하지 않은 경우 422 테스트
    """

    res = client.get("/terms?ids=invalid")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_retrieve_terms_data_not_found():
    """
    요청한 약관 ID가 모두 존재하지 않는 경우 404 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise DataNotFoundException

    mock_pg_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch.object(RetrieveTermsService, "exec", side_effect=mock_exec):
        res = client.get("/terms?ids=999")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_retrieve_terms_db_server_error():
    """
    DB 서버와의 통신 오류가 발생한 경우 502 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise DBServerException

    mock_pg_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch.object(RetrieveTermsService, "exec", side_effect=mock_exec):
        res = client.get("/terms?ids=1")
        assert res.status_code == 502


@pytest.mark.asyncio
async def test_retrieve_terms_internal_server_error():
    """
    원인 불명의 내부 로직 오류가 발생한 경우 500 테스트
    """

    async def mock_exec(*args, **kwargs):
        raise Exception

    mock_pg_session = mock.MagicMock()

    with mock.patch(
        "app.api.dep.get_pg_session",
        return_value=mock_pg_session,
    ), mock.patch.object(RetrieveTermsService, "exec", side_effect=mock_exec):
        res = client.get("/terms?ids=1")
        assert res.status_code == 500
