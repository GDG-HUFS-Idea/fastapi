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
)
async def retrieve_terms(
    dto: Annotated[RetrieveTermsUsecaseDTO, Depends()],
    usecase: RetrieveTermsUsecase = Depends(get_retrieve_terms_usecase),
):
    return await usecase.execute(dto)
