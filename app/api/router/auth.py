from typing import Annotated
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import RedirectResponse

from app.api.dep import get_pg_session, get_redis_session
from app.service.auth.handle_oauth_callback import (
    HandleOAuthCallbackService,
    HandleOAuthCallbackServiceDTO,
)
from app.service.auth.oauth_signup import (
    OAuthSignupService,
    OAuthSignupServiceDTO,
    OAuthSignupServiceResponse,
)
from app.service.auth.redirect_oauth import (
    RedirectOAuthService,
    RedirectOAuthServiceDTO,
)
from app.service.auth.retrieve_oauth_result import (
    RetrieveOAuthResultService,
    RetrieveOAuthResultServiceDTO,
    RetrieveOAuthResultServiceResponse,
)
from app.util.enum import UserRole


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    path="/oauth/signup",
    status_code=201,
    response_model=OAuthSignupServiceResponse,
    response_model_exclude_none=True,
    responses={
        201: {
            "description": "OAuth 로그인을 통한 회원가입이 성공적으로 처리됨",
            "content": {
                "application/json": {
                    "example": {
                        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user_id": 2,
                        "roles": [UserRole.GENERAL],
                        "name": "홍길동",
                    }
                }
            },
        },
        400: {
            "description": "FieldMissingException: 요청에 필수 필드(code, term_agreements)가 "
            "누락되었거나, 필수 동의 항목에 동의하지 않았거나, 요청 객체에 클라이언트 호스트 정보가 없음"
        },
        422: {
            "description": "ValidationException: 제출된 약관 동의 정보와 "
            "필요한 약관 정보가 일치하지 않는 등 데이터 유효성 검증에 실패함"
        },
        403: {
            "description": "NoPermissionException: 요청한 code에 저장된 "
            "호스트 정보와 현재 요청의 호스트가 다르거나 접근 권한이 없음"
        },
        404: {
            "description": "DataNotFoundException: 요청한 OAuth 인증 코드에 "
            "해당하는 프로필 정보를 캐시 서버에서 찾을 수 없거나, 필요한 약관 정보가 사전에 DB에 존재하지 않음"
        },
        500: {
            "description": "JWT 토큰 생성 과정에서 오류가 발생하거나, 원인 불명의 내부 로직 오류가 발생함"
        },
        502: {
            "description": "DBServerException/CacheServerException: 사용자 정보 저장, "
            "약관 동의 저장, 약관 정보 조회 중 DB 서버 오류가 발생하거나, "
            "OAuth 프로필 정보 조회 중 캐시 서버와의 통신 오류가 발생함"
        },
    },
)
async def oauth_signup(
    req: Request,
    dto: Annotated[OAuthSignupServiceDTO, Body()],
    pg_session=Depends(get_pg_session),
    redis_session=Depends(get_redis_session),
):
    return await OAuthSignupService(pg_session, redis_session).exec(req, dto)


@auth_router.get(
    path="/oauth/result",
    status_code=200,
    response_model=RetrieveOAuthResultServiceResponse,
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "OAuth 인증 결과를 성공적으로 조회함",
            "content": {
                "application/json": {
                    "examples": {
                        "이미 계정이 있는 사용자": {
                            "value": {
                                "has_account": True,
                                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "user_id": 123,
                                "roles": [UserRole.GENERAL],
                                "name": "홍길동",
                            }
                        },
                        "계정이 없는 신규 사용자": {
                            "value": {
                                "has_account": False,
                                "code": "FYVjdmoq9RQ2UPYu_cCRhA",
                                "signup_term_ids": [1, 2, 3],
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "FieldMissingException: 요청에 필수 파라미터가 "
            "누락되었거나, 요청 객체에 클라이언트 정보가 없음"
        },
        403: {
            "description": "NoPermissionException: 요청 호스트와 OAuth 프로필의 "
            "호스트가 일치하지 않음"
        },
        404: {
            "description": "DataNotFoundException: OAuth 프로필을 찾을 수 없거나 "
            "필요한 약관 정보가 존재하지 않음"
        },
        422: {
            "description": "ValidationException: 요청 데이터의 형식이 올바르지만 "
            "비즈니스 규칙에 따른 유효성 검증에 실패함"
        },
        500: {"description": "원인 불명의 내부 로직 오류가 발생함"},
        502: {
            "description": "CacheServerException/DBServerException: Redis 캐시 서버나 "
            "데이터베이스 서버와의 통신 중 오류가 발생함"
        },
    },
)
async def retrieve_oauth_result(
    req: Request,
    dto: Annotated[RetrieveOAuthResultServiceDTO, Depends()],
    pg_session=Depends(get_pg_session),
    redis_session=Depends(get_redis_session),
):
    return await RetrieveOAuthResultService(pg_session, redis_session).exec(
        req, dto
    )


@auth_router.get(
    path="/oauth/{provider}",
    status_code=307,
    response_class=RedirectResponse,
    responses={
        307: {
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
        500: {"description": "원인 불명의 내부 로직 오류가 발생함"},
        502: {
            "description": "OAuthServerException: 외부 OAuth 인증 서버와의 "
            "통신 중 오류가 발생하거나, OAuth 서버가 비정상적인 응답을 반환함"
        },
    },
)
async def redirect_oauth(
    req: Request,
    dto: Annotated[RedirectOAuthServiceDTO, Depends()],
):
    return await RedirectOAuthService().exec(req, dto)


@auth_router.get(
    path="/oauth/{provider}/callback",
    name="handle_oauth_callback",
    response_class=RedirectResponse,
    status_code=307,
    responses={
        307: {
            "description": "OAuth 인증 완료 후 프론트엔드 리다이렉트 URL로 성공적으로 리다이렉트됨"
        },
        400: {
            "description": "FieldMissingException: 요청에 필수 파라미터가 "
            "누락되었거나, 요청 객체에 클라이언트 정보가 없음"
        },
        403: {
            "description": "CSRFException: OAuth state 값이 일치하지 않아 "
            "CSRF 공격 가능성이 감지됨"
        },
        422: {
            "description": "ValidationException: 지원하지 않는 인증 제공자(provider) "
            "값이 전달되었거나, provider 값의 형식이 올바르지 않음"
        },
        500: {"description": "원인 불명의 내부 로직 오류가 발생함"},
        502: {
            "description": "OAuthServerException/CacheServerException: 외부 OAuth 서버에서 "
            "프로필 정보를 가져오는 중 오류가 발생하거나, 프로필 정보를 "
            "캐시 서버에 저장하는 중 통신 오류가 발생함"
        },
    },
)
async def handle_oauth_callback(
    req: Request,
    dto: Annotated[HandleOAuthCallbackServiceDTO, Depends()],
    redis_session=Depends(get_redis_session),
):
    return await HandleOAuthCallbackService(redis_session).exec(req, dto)
