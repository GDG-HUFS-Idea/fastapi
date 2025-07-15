from datetime import datetime
from typing import List, Optional
from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import TermType
from app.repository.term import TermRepository
from app.common.exceptions import UsecaseException, NotFoundException, InternalServerException, RepositoryError


class RetrieveTermsUsecaseDTO(BaseModel):
    ids: List[int] = Field(Query(min_length=1, description="조회할 약관 ID 목록"))

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ids": [1, 2, 4],
                }
            ]
        }
    )


class _Term(BaseModel):
    id: int = Field(description="약관 ID")
    title: str = Field(description="약관 제목")
    type: TermType = Field(description="약관 타입")
    version: str = Field(description="약관 버전")
    is_required: bool = Field(description="필수 약관 여부")
    content: str = Field(description="약관 내용")
    created_at: datetime = Field(description="약관 생성일시")


class RetrieveTermsUsecaseResponse(BaseModel):
    terms: List[_Term] = Field(
        description="조회된 약관 목록",
    )
    missing_ids: Optional[List[int]] = Field(
        default=None,
        description="존재하지 않는 약관 ID 목록",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "terms": [
                        {
                            "id": 1,
                            "title": "서비스 이용약관",
                            "type": "terms_of_service",
                            "version": "1.0",
                            "is_required": True,
                            "content": "본 약관은 회사가 제공하는 서비스의 이용 조건을 규정합니다.",
                            "created_at": "2025-07-11T06:17:34.604304Z",
                        },
                        {
                            "id": 2,
                            "title": "개인정보처리방침",
                            "type": "privacy_policy",
                            "version": "1.0",
                            "is_required": True,
                            "content": "회사는 개인정보보호법에 따라 이용자의 개인정보를 보호합니다.",
                            "created_at": "2025-07-11T06:17:34.604304Z",
                        },
                    ],
                    "missing_ids": [4],
                }
            ]
        }
    )


class RetrieveTermsUsecase:
    def __init__(
        self,
        term_repository: TermRepository,
    ) -> None:
        self._term_repository = term_repository

    async def execute(
        self,
        dto: RetrieveTermsUsecaseDTO,
    ) -> RetrieveTermsUsecaseResponse:
        try:
            # 1. 요청된 약관 ID 목록으로 약관 조회
            terms = await self._term_repository.find_many_by_ids(dto.ids)
            if not terms:
                raise NotFoundException("요청된 약관을 찾을 수 없습니다")

            # 2. 조회 결과 분석 및 누락된 ID 확인
            found_term_ids = {term.id for term in terms}
            missing_term_ids = list(set(dto.ids) - found_term_ids) or None

            # 3. 약관 정보를 응답 형태로 변환하여 반환
            term_responses = [_Term.model_validate(term.model_dump()) for term in terms]
            return RetrieveTermsUsecaseResponse(
                terms=term_responses,
                missing_ids=missing_term_ids,
            )

        except RepositoryError as exception:
            raise InternalServerException(f"데이터베이스 조회 중 오류가 발생했습니다: {str(exception)}") from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            raise InternalServerException(f"약관 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
