from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.common.enums import TermType
from app.repository.term import TermRepository
from app.common.exceptions import UsecaseException, NotFoundException, InternalServerException, RepositoryError


class RetrieveTermsUsecaseDTO(BaseModel):
    ids: List[int] = Field()


class _Term(BaseModel):
    id: int
    title: str
    type: TermType
    content: str
    is_required: bool
    created_at: datetime
    updated_at: datetime


class RetrieveTermsUsecaseResponse(BaseModel):
    terms: List[_Term]
    missing_ids: Optional[List[int]] = None


class RetrieveTermsUsecase:
    def __init__(self, term_repository: TermRepository) -> None:
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
            raise InternalServerException(f"약관 조회 중 데이터베이스 오류가 발생했습니다: {str(exception)}") from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            raise InternalServerException(f"약관 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
