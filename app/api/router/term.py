from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.dep import get_pg_session
from app.service.term.retrieve_terms import (
    RetrieveTermsService,
    RetrieveTermsServiceDTO,
    RetrieveTermsServiceResponse,
)
from app.util.enum import TermType


term_router = APIRouter(prefix="/terms", tags=["term"])


@term_router.get(
    path="",
    status_code=200,
    response_model=RetrieveTermsServiceResponse,
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "요청한 약관 정보를 성공적으로 조회함",
            "content": {
                "application/json": {
                    "examples": {
                        "전체 약관 정보 조회 성공": {
                            "value": {
                                "terms": [
                                    {
                                        "id": 1,
                                        "title": "서비스 이용약관",
                                        "type": TermType.TERMS_OF_SERVICE,
                                        "content": "본 약관은 서비스 이용에 관한 약관입니다...",
                                        "is_required": True,
                                        "created_at": "2024-05-01T09:30:00.000Z",
                                        "updated_at": "2024-05-01T09:30:00.000Z",
                                    },
                                    {
                                        "id": 2,
                                        "title": "개인정보 처리방침",
                                        "type": TermType.PRIVACY_POLICY,
                                        "content": "개인정보 처리방침 내용입니다...",
                                        "is_required": True,
                                        "created_at": "2024-05-01T09:35:00.000Z",
                                        "updated_at": "2024-05-01T09:35:00.000Z",
                                    },
                                ]
                            }
                        },
                        "일부 약관 ID 누락": {
                            "value": {
                                "terms": [
                                    {
                                        "id": 1,
                                        "title": "서비스 이용약관",
                                        "type": TermType.TERMS_OF_SERVICE,
                                        "content": "본 약관은 서비스 이용에 관한 약관입니다...",
                                        "is_required": True,
                                        "created_at": "2024-05-01T09:30:00.000Z",
                                        "updated_at": "2024-05-01T09:30:00.000Z",
                                    }
                                ],
                                "missing_ids": [2, 3],
                            }
                        },
                    }
                }
            },
        },
        400: {
            "description": "FieldMissingException: 요청에 필수 쿼리 파라미터(ids)가 "
            "누락되었거나, 요청된 파라미터의 형식이 올바르지 않음"
        },
        422: {
            "description": "ValidationException: 요청된 term ID 목록의 형식이 "
            "유효하지 않거나, 허용되지 않는 값이 포함됨"
        },
        404: {
            "description": "DataNotFoundException: 요청한 약관 ID가 모두 존재하지 않거나, "
            "DB에서 해당 ID에 해당하는 약관 정보를 찾을 수 없음"
        },
        500: {
            "description": "InternalLogicException: 약관 정보 처리 과정에서 "
            "오류가 발생하거나, 원인 불명의 내부 로직 오류가 발생함"
        },
        502: {
            "description": "DBServerException: 약관 정보 조회 중 DB 서버와의 "
            "통신 오류가 발생하거나, DB 서버가 비정상적인 응답을 반환함"
        },
    },
)
async def retrieve_terms(
    dto: Annotated[RetrieveTermsServiceDTO, Depends()],
    pg_session=Depends(get_pg_session),
):
    return await RetrieveTermsService(pg_session).exec(dto)
