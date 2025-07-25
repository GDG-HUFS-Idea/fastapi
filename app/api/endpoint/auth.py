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
    responses={
        200: {
            "description": "OAuth 결과 조회 성공 - 기존 사용자는 토큰과 사용자 정보, 신규 사용자는 임시 코드와 약관 목록 반환",
            "content": {
                "application/json": {
                    "examples": {
                        "기존 사용자": {
                            "summary": "계정이 있는 경우",
                            "value": {
                                "has_account": True,
                                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "user_id": 1,
                                "name": "suehyun lee",
                                "roles": ["general"],
                            },
                        },
                        "신규 사용자": {
                            "summary": "계정이 없는 경우",
                            "value": {"has_account": False, "code": "dx8E5HLSE_nCsP6kQKUY7g", "active_term_ids": [1, 2, 3]},
                        },
                    }
                }
            },
        },
        401: {"description": "인증 실패 - 클라이언트 호스트 정보를 조회할 수 없는 경우"},
        403: {"description": "접근 권한 없음 - 요청한 호스트와 OAuth 프로필의 호스트가 일치하지 않는 경우"},
        404: {"description": "OAuth 프로필을 찾을 수 없는 경우"},
        422: {"description": "검증 오류 - authorization code가 유효하지 않은 경우"},
        500: {"description": "서버 내부 오류 - 캐시, 저장소, JWT 처리 오류 또는 예상치 못한 오류 발생"},
    },
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
    responses={
        200: {"description": "OAuth 회원가입 성공 - JWT 토큰과 사용자 정보 반환"},
        401: {"description": "인증 실패 - 클라이언트 호스트 정보를 조회할 수 없는 경우"},
        403: {"description": "접근 권한 없음 - 요청한 호스트와 OAuth 프로필의 호스트가 일치하지 않는 경우"},
        404: {"description": "OAuth 프로필을 찾을 수 없는 경우"},
        422: {"description": "검증 오류 - 요청 유효하지 않은 데이터 및 약관 ID, 필수 약관 미동의, 또는 누락된 약관이 있는 경우"},
        500: {"description": "서버 내부 오류 - JWT, 저장소, 캐시 처리 오류 또는 예상치 못한 오류 발생"},
    },
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
    responses={
        307: {"description": "OAuth 제공자 인증 페이지로 리다이렉트 성공"},
        422: {"description": "검증 오류 - 지원하지 않는 OAuth 제공자이거나 frontend_redirect_url이 유효하지 않은 경우"},
        500: {"description": "서버 내부 오류 - OAuth 서비스 오류 또는 예상치 못한 오류 발생"},
    },
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
    include_in_schema=False,
    status_code=307,
    response_class=RedirectResponse,
)
async def handle_oauth_callback(
    request: Request,
    dto: Annotated[HandleOAuthCallbackUsecaseDTO, Depends()],
    usecase: HandleOAuthCallbackUsecase = Depends(get_handle_oauth_callback_usecase),
):
    return await usecase.execute(request, dto)
