from functools import lru_cache
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client.errors import MismatchingStateError
from fastapi import Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ValidationError

from app.common.enums import OauthProvider
from app.core.config import setting
from app.common.exceptions import OAuthRedirectError, OAuthStateError, OAuthProfileError, OAuthDataCorruptedError


@lru_cache(maxsize=1)
def _create_oauth() -> OAuth:
    oauth = OAuth()
    oauth.register(
        name=OauthProvider.GOOGLE.value,
        client_id=setting.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=setting.GOOGLE_OAUTH_SECRET,
        access_token_url="https://oauth2.googleapis.com/token",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        api_base_url="https://www.googleapis.com/oauth2/v1/",
        jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
        client_kwargs={"scope": "openid email profile"},
    )
    return oauth


class RawOAuthProfile(BaseModel):
    name: str
    email: str


class OAuthService:
    def __init__(self) -> None:
        self._oauth_client = _create_oauth()

    async def redirect_authorization(
        self,
        request: Request,
        provider: OauthProvider,
    ) -> RedirectResponse:
        try:
            client = self._oauth_client.create_client(provider.value)
            redirect_url = request.url_for("handle_oauth_callback", provider=provider.value)

            return await client.authorize_redirect(request, redirect_uri=redirect_url)  # type: ignore

        except MismatchingStateError as exception:
            raise OAuthStateError(f"OAuth 인증 상태가 일치하지 않습니다: {str(exception)}") from exception
        except Exception as exception:
            raise OAuthRedirectError(f"OAuth 인증 리다이렉트 중 오류가 발생했습니다: {str(exception)}") from exception

    async def fetch_raw_oauth_profile(
        self,
        request: Request,
        provider: OauthProvider,
    ) -> RawOAuthProfile:
        try:
            client = self._oauth_client.create_client(provider.value)

            token = await client.authorize_access_token(request)  # type: ignore
            response = await client.get("userinfo", token=token)  # type: ignore
            user_info = response.json()

            return RawOAuthProfile.model_validate(user_info)

        except ValidationError as exception:
            raise OAuthDataCorruptedError(f"OAuth 프로필 데이터 형식이 올바르지 않습니다: {str(exception)}") from exception
        except Exception as exception:
            raise OAuthProfileError(f"OAuth 프로필 조회 중 오류가 발생했습니다: {str(exception)}") from exception
