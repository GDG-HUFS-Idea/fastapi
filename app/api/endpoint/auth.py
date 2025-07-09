from typing import Annotated
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import RedirectResponse

from app.core.dependency import (
    get_handle_oauth_callback_usecase,
    get_oauth_sign_up_usecase,
    get_redirect_oauth_usecase,
    get_retrieve_oauth_result_usecase,
)
from app.usecase.auth.handle_oauth_callback import HandleOAuthCallbackUsecase, HandleOAuthCallbackUsecaseDTO
from app.usecase.auth.oauth_sign_up import OAuthSignUpUsecase, OAuthSignUpUsecaseDTO, OAuthSignUpUsecaseResponse
from app.usecase.auth.redirect_oauth import RedirectOAuthUsecase, RedirectOAuthUsecaseDTO
from app.usecase.auth.retrieve_oauth_result import (
    RetrieveOAuthResultUsecase,
    RetrieveOAuthResultUsecaseDTO,
    RetrieveOAuthResultUsecaseResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get(
    path="/oauth/result",
    status_code=200,
    response_model=RetrieveOAuthResultUsecaseResponse,
    response_model_exclude_none=True,
)
async def retrieve_oauth_result(
    request: Request,
    dto: Annotated[RetrieveOAuthResultUsecaseDTO, Depends()],
    usecase: RetrieveOAuthResultUsecase = Depends(get_retrieve_oauth_result_usecase),
):
    return await usecase.execute(request, dto)


@auth_router.post(
    path="/oauth/signup",
    status_code=200,
    response_model=OAuthSignUpUsecaseResponse,
    response_model_exclude_none=True,
)
async def oauth_signup(
    request: Request,
    dto: Annotated[OAuthSignUpUsecaseDTO, Body()],
    usecase: OAuthSignUpUsecase = Depends(get_oauth_sign_up_usecase),
):
    return await usecase.execute(request, dto)


@auth_router.get(
    path="/oauth/{provider}",
    status_code=307,
    response_class=RedirectResponse,
)
async def redirect_oauth(
    request: Request,
    dto: Annotated[RedirectOAuthUsecaseDTO, Depends()],
    usecase: RedirectOAuthUsecase = Depends(get_redirect_oauth_usecase),
):
    return await usecase.execute(request, dto)


@auth_router.get(
    path="/oauth/{provider}/callback",
    name="handle_oauth_callback",
    status_code=307,
    response_class=RedirectResponse,
)
async def handle_oauth_callback(
    request: Request,
    dto: Annotated[HandleOAuthCallbackUsecaseDTO, Depends()],
    usecase: HandleOAuthCallbackUsecase = Depends(get_handle_oauth_callback_usecase),
):
    return await usecase.execute(request, dto)
