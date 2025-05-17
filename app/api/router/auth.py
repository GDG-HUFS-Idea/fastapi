from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.service.auth.redirect_oauth import (
    RedirectOAuthService,
    RedirectOAuthServiceDTO,
)


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get(
    path="/oauth/{provider}",
    status_code=302,
    response_class=RedirectResponse,
    responses={
        302: {
            "description": "인증 제공자(provider)의 로그인 페이지로 성공적으로 리다이렉트됨"
        },
        400: {
            "description": "FieldMissingException: 요청에 필수 파라미터가 "
            "누락되었거나, 요청 객체에 클라이언트 정보가 없음"
        },
        422: {
            "description": "ValidationException: 지원하지 않는 인증 제공자(provider) "
            "값이 전달되었거나, provider 값의 형식이 올바르지 않음"
        },
        500: {
            "description": "InternalLogicException: OAuth 인증 URI 생성 과정에서 "
            "오류가 발생하거나, 원인 불명의 내부 로직 오류가 발생함"
        },
        502: {
            "description": "OAuthServerException: 외부 OAuth 인증 서버와의 "
            "통신 중 오류가 발생하거나, OAuth 서버가 비정상적인 응답을 반환함"
        },
    },
)
async def redirect_oauth(
    req: Request,
    dto: Annotated[RedirectOAuthServiceDTO, Depends()],
    service=RedirectOAuthService(),
):
    return await service.exec(req, dto)


@auth_router.get(
    path="/oauth/{provider}/callback",
    name="handle_oauth_callback",
)
async def handle_oauth_callback(
    req: Request,
):
    return
