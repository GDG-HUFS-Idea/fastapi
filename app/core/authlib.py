from functools import lru_cache
from authlib.integrations.starlette_client import OAuth

from app.util.enum import OauthProvider
from app.core.config import env


oauth = OAuth()
oauth.register(
    name=OauthProvider.GOOGLE.value,
    client_id=env.google_oauth_client_id,
    client_secret=env.google_oauth_secret,
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    client_kwargs={"scope": "openid email profile"},
)
