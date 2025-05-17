from fastapi import Path, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.util.enum import OauthProvider
from app.util.exception import OAuthServerException
from app.core.authlib import oauth


class RedirectOAuthServiceDTO(BaseModel):
    provider: OauthProvider = Field(Path(description="OAuth 인증 제공자"))


class RedirectOAuthService:
    async def exec(
        self, req: Request, dto: RedirectOAuthServiceDTO
    ) -> RedirectResponse:
        return await self.authorize_redirect(req, dto.provider)

    async def authorize_redirect(
        self, req: Request, provider: OauthProvider
    ) -> RedirectResponse:
        """
        OAuth 인증을 위해 사용자를 로그인 페이지로 리다이렉트
        """
        try:
            client = oauth.create_client(provider)
            redirect_uri = req.url_for(
                "handle_oauth_callback", provider=provider.value
            )

            return await client.authorize_redirect(req, redirect_uri=redirect_uri)  # type: ignore
        except Exception as exc:
            raise OAuthServerException from exc
