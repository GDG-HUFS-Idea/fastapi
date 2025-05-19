from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.dep import get_pg_session
from app.service.term.retrieve_terms import (
    RetrieveTermsService,
    RetrieveTermsServiceDTO,
    RetrieveTermsServiceResponse,
)


term_router = APIRouter(prefix="/terms", tags=["term"])


@term_router.get(
    path="",
    status_code=200,
    response_model=RetrieveTermsServiceResponse,
    response_model_exclude_none=True,
)
async def retrieve_terms(
    dto: Annotated[RetrieveTermsServiceDTO, Depends()],
    pg_session=Depends(get_pg_session),
):
    return await RetrieveTermsService(pg_session).exec(dto)
