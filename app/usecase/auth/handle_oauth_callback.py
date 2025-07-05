from datetime import timedelta
from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.common.enums import OauthProvider
from app.service.auth.oauth import OAuthService
from app.service.cache.oauth_profile import OAuthProfile, OAuthProfileCache
from app.common.exceptions import (
    UsecaseException,
    UnauthorizedException,
    NotFoundException,
    InternalServerException,
    OAuthError,
    CacheError,
)


class HandleOAuthCallbackUsecaseDTO(BaseModel):
    provider: OauthProvider = Field()
    code: str = Field(min_length=10)


class HandleOAuthCallbackUsecase:
    _UNTIL_CALLBACK_EXPIRE_DELTA = timedelta(minutes=2)

    def __init__(
        self,
        oauth_service: OAuthService,
        oauth_profile_cache: OAuthProfileCache,
    ):
        self._oauth_service = oauth_service
        self._oauth_profile_cache = oauth_profile_cache

    async def execute(
        self,
        request: Request,
        dto: HandleOAuthCallbackUsecaseDTO,
    ) -> RedirectResponse:
        try:
            # 1. 클라이언트 정보 및 리다이렉트 URL 검증
            host: Optional[str] = getattr(request.client, "host", None)
            if not host:
                raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

            frontend_redirect_url: Optional[str] = request.session.get("frontend_redirect_url")
            if not frontend_redirect_url:
                raise NotFoundException("프론트엔드 리다이렉트 URL이 세션에 없습니다")

            # 2. OAuth 제공자로부터 사용자 프로필 조회
            oauth_profile = await self._fetch_oauth_profile(request, dto, host)

            # 3. 조회한 프로필을 캐시에 임시 저장
            key = await self._oauth_profile_cache.set(
                data=oauth_profile,
                expire_delta=self._UNTIL_CALLBACK_EXPIRE_DELTA,
            )

            # 4. 프론트엔드로 결과 코드와 함께 리다이렉트
            final_frontend_redirect_url = f"{frontend_redirect_url}?code={key}"
            return RedirectResponse(final_frontend_redirect_url)

        except OAuthError as exception:
            raise InternalServerException(f"OAuth 처리 중 오류가 발생했습니다: {str(exception)}") from exception
        except CacheError as exception:
            raise InternalServerException(f"캐시 처리 중 오류가 발생했습니다: {str(exception)}") from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            raise InternalServerException(f"OAuth 콜백 처리 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def _fetch_oauth_profile(
        self,
        request: Request,
        dto: HandleOAuthCallbackUsecaseDTO,
        host: str,
    ) -> OAuthProfile:
        raw_oauth_profile = await self._oauth_service.fetch_raw_oauth_profile(
            request=request,
            provider=dto.provider,
        )

        return OAuthProfile(
            name=raw_oauth_profile.name,
            email=raw_oauth_profile.email,
            host=host,
        )
