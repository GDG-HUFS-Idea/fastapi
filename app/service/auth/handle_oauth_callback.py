from datetime import timedelta
from fastapi import Path, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from authlib.integrations.base_client.errors import MismatchingStateError

from app.core.config import env
from app.util.exception import (
    CSRFException,
    FieldMissingException,
    OAuthServerException,
    CacheServerException,
)
from app.util.enum import OauthProvider
from app.core.authlib import oauth
from app.cache.oauth_profile import OAuthProfileCache
from app.util.schema import OAuthProfile, RawProfile


class HandleOAuthCallbackServiceDTO(BaseModel):
    provider: OauthProvider = Field(Path(description="OAuth 인증 제공자"))
    code: str = Field(
        Query(description="OAuth 인증 코드", min_length=10, max_length=50)
    )


class HandleOAuthCallbackService:
    def __init__(self, redis_session: Redis):
        self.oauth_profile_cache = OAuthProfileCache(session=redis_session)

    async def exec(
        self, req: Request, dto: HandleOAuthCallbackServiceDTO
    ) -> RedirectResponse:
        host = self.extract_host(req)
        raw_profile = await self.fetch_profile(req, dto.provider)
        profile_id = await self.set_oauth_profile(raw_profile, host)
        redirect_url = self.generate_redirect_url(profile_id)

        return RedirectResponse(redirect_url)

    def extract_host(self, req: Request) -> str:
        """
        요청 객체에서 클라이언트 domain host 추출 (host를 통해 결과 조회 시 소유자 확인)
        """
        try:
            return getattr(req.client, "host")
        except Exception as exc:
            raise FieldMissingException from exc

    async def fetch_profile(
        self, req: Request, provider: OauthProvider
    ) -> RawProfile:
        """
        OAuth 인증 서버에서 프로필 정보 조회
        """
        try:
            client = oauth.create_client(provider)
            token = await client.authorize_access_token(req)  # type: ignore
            oauth_profile = await client.get("userinfo", token=token)  # type: ignore

            profile_json = oauth_profile.json()

            return RawProfile(
                name=profile_json["name"], email=profile_json["email"]
            )
        except MismatchingStateError as exc:
            raise CSRFException from exc
        except Exception as exc:
            raise OAuthServerException from exc

    async def set_oauth_profile(
        self, raw_profile: RawProfile, host: str
    ) -> str:
        """
        결과 조회를 위해 Redis에 프로필 정보 임시 저장 (2분 후 만료)
        """
        try:
            return await self.oauth_profile_cache.set(
                oauth_profile=OAuthProfile(
                    name=raw_profile.name,
                    email=raw_profile.email,
                    host=host,
                ),
                expire_delta=timedelta(minutes=2),
            )
        except Exception as exc:
            raise CacheServerException from exc

    def generate_redirect_url(self, profile_id: str) -> str:
        """
        클라이언트에게 전달할 리다이렉트 URL 생성
        """
        redirect_url = f"{env.frontend_redirect_url}?code={profile_id}"
        return redirect_url
