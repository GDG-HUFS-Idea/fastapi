from fastapi import Path, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import OauthProvider
from app.service.auth.oauth import OAuthService
from app.common.exceptions import InternalServerException, OAuthError


class RedirectOAuthUsecaseDTO(BaseModel):
    provider: OauthProvider = Field(Path(description="OAuth 제공자"))
    frontend_redirect_url: str = Field(Query(min_length=1, max_length=500, description="OAuth 인증 완료 후 리다이렉트할 프론트엔드 URL"))

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "provider": "google",
                    "frontend_redirect_url": "http://localhost:3000/auth/callback",
                },
            ]
        }
    )


class RedirectOAuthUsecase:
    def __init__(
        self,
        oauth_service: OAuthService,
    ) -> None:
        self._oauth_service = oauth_service

    async def execute(
        self,
        request: Request,
        dto: RedirectOAuthUsecaseDTO,
    ) -> RedirectResponse:
        try:
            # 1. 프론트엔드 리다이렉트 URL을 세션에 저장
            request.session["frontend_redirect_url"] = dto.frontend_redirect_url

            # 2. OAuth 제공자 인증 페이지로 리다이렉트
            return await self._oauth_service.redirect_authorization(
                request=request,
                provider=dto.provider,
            )

        except OAuthError as exception:
            raise InternalServerException(str(exception)) from exception
        except Exception as exception:
            raise InternalServerException(f"OAuth 리다이렉트 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
