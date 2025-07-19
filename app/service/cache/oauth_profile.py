from pydantic import BaseModel
from redis.asyncio import Redis

from app.service.cache.base import BaseCache


class OAuthProfile(BaseModel):
    email: str
    name: str
    host: str


class OAuthProfileCache(BaseCache[OAuthProfile]):
    _BASE_KEY = "oauth_profile"
    _DATA_CLASS = OAuthProfile

    def __init__(
        self,
        session: Redis,
    ) -> None:
        super().__init__(session)
