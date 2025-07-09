from typing import Optional
from redis.asyncio import Redis
import secrets
from datetime import timedelta

from app.util.schema import OAuthProfile


class OAuthProfileCache:
    base = "profile"

    def __init__(self, session: Redis):
        self.session = session

    async def set(
        self, oauth_profile: OAuthProfile, expire_delta: timedelta
    ) -> str:
        """
        OAuth 프로필 정보 임시 저장
        """
        profile_json = oauth_profile.model_dump_json()
        id = secrets.token_urlsafe(16)

        expire_in = int(expire_delta.total_seconds())

        await self.session.setex(
            name=f"{self.base}:{id}", time=expire_in, value=profile_json
        )

        return id

    async def get(self, id: str) -> Optional[OAuthProfile]:
        """
        OAuth 프로필 정보 조회
        """
        profile_json = await self.session.get(f"{self.base}:{id}")

        if profile_json is None:
            return None

        return OAuthProfile.model_validate_json(profile_json)

    async def evict(self, id: str) -> bool:
        """
        OAuth 프로필 정보 삭제
        """
        result = await self.session.delete(f"{self.base}:{id}")

        return result > 0
