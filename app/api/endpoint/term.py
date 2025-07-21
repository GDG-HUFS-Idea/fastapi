from typing import Annotated

from fastapi import APIRouter, Depends
from app.core.dependency import get_retrieve_terms_usecase
from app.usecase.term.retrieve_terms import RetrieveTermsUsecase, RetrieveTermsUsecaseDTO, RetrieveTermsUsecaseResponse

term_router = APIRouter(prefix="/terms", tags=["term"])


@term_router.get(
    path="",
    status_code=200,
    response_model=RetrieveTermsUsecaseResponse,
    response_model_exclude_none=True,
    responses={
        200: {"description": "약관 조회 성공 - 존재하는 약관 목록과 누락된 ID 목록 반환"},
        404: {"description": "요청된 약관을 찾을 수 없는 경우"},
        422: {"description": "검증 오류 - 약관 ID 목록이 유효하지 않은 경우"},
        500: {"description": "서버 내부 오류 - 데이터베이스 조회 오류 또는 예상치 못한 오류 발생"},
    },
)
async def retrieve_terms(
    dto: Annotated[RetrieveTermsUsecaseDTO, Depends()],
    usecase: RetrieveTermsUsecase = Depends(get_retrieve_terms_usecase),
):
    return await usecase.execute(dto)
