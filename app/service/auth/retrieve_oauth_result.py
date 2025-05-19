from datetime import timedelta
from typing import List, Optional
from fastapi import Query, Request
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession


from app.cache.oauth_profile import OAuthProfileCache
from app.db.model.user import User
from app.repo.term import TermRepo
from app.repo.user import UserRepo
from app.util.enum import UserRole, TermType
from app.util.exception import (
    CacheServerException,
    DBServerException,
    FieldMissingException,
    NoPermissionException,
    DataNotFoundException,
)
from app.util.jwt import jwt_encode
from app.util.schema import OAuthProfile, Payload


class RetrieveOAuthResultServiceDTO(BaseModel):
    code: str = Field(
        Query(
            description="OAuth 인증 결과 소유자 식별 코드",
            min_length=10,
            max_length=50,
        ),
    )


class RetrieveOAuthResultServiceResponse(BaseModel):
    has_account: bool
    token: Optional[str] = None
    user_id: Optional[int] = None
    roles: Optional[List[UserRole]] = None
    name: Optional[str] = None
    code: Optional[str] = None
    signup_term_ids: Optional[List[int]] = None


class RetrieveOAuthResultService:
    def __init__(self, pg_session: AsyncSession, redis_session: Redis):
        self.user_repo = UserRepo(pg_session)
        self.term_repo = TermRepo(pg_session)
        self.oauth_profile_cache = OAuthProfileCache(redis_session)

    async def exec(
        self, req: Request, dto: RetrieveOAuthResultServiceDTO
    ) -> RetrieveOAuthResultServiceResponse:
        host = self.extract_host(req)
        oauth_profile = await self.get_oauth_profile(dto.code, host)
        user = await self.retrieve_user(oauth_profile.email)
        has_account = bool(user)

        if has_account:
            token = self.sign_token(user)
            await self.evict_oauth_profile(dto.code)

            return RetrieveOAuthResultServiceResponse(
                has_account=True,
                token=token,
                user_id=user.id,
                roles=user.roles,
                name=user.name,
            )
        else:
            profile_id = await self.set_oauth_profile(oauth_profile)
            signup_term_ids = await self.retrieve_signup_term_ids()
            await self.evict_oauth_profile(dto.code)

            return RetrieveOAuthResultServiceResponse(
                has_account=False,
                code=profile_id,
                signup_term_ids=signup_term_ids,
            )

    def extract_host(self, req: Request) -> str:
        """
        요청 객체에서 클라이언트 domain host 추출
        """

        try:
            return getattr(req.client, "host")
        except Exception as exc:
            raise FieldMissingException from exc

    async def get_oauth_profile(self, id: str, host: str) -> OAuthProfile:
        """
        전달된 code의 OAuth profile 조회 후 추출한 host와 비교
        """

        try:
            oauth_profile = await self.oauth_profile_cache.get(id)
        except Exception as exc:
            raise CacheServerException from exc

        if not oauth_profile:
            raise DataNotFoundException
        elif oauth_profile.host != host:
            raise NoPermissionException

        return oauth_profile

    async def retrieve_user(self, email: str) -> Optional[User]:
        """
        이메일로 사용자 조회
        """

        try:
            return await self.user_repo.find_by_email(email)
        except Exception as exc:
            raise DBServerException from exc

    def sign_token(self, user: User) -> str:
        """
        JWT 토큰 생성
        """

        return jwt_encode(
            payload=Payload(
                id=user.id,  # type: ignore
                name=user.name,
                roles=user.roles,
            ),
            expire_delta=timedelta(days=3),
        )

    async def evict_oauth_profile(self, id: str) -> bool:
        """
        앞선 서비스 flow의 HandleOAuthCallback에서 캐싱되었던 OAuth profile 삭제
        """

        try:
            return await self.oauth_profile_cache.evict(id)
        except Exception as exc:
            raise CacheServerException from exc

    async def set_oauth_profile(self, oauth_profile: OAuthProfile) -> str:
        """
        다시 신규 OAuth profile 저장
        """

        try:
            return await self.oauth_profile_cache.set(
                oauth_profile=oauth_profile,
                expire_delta=timedelta(minutes=15),
            )
        except Exception as exc:
            raise CacheServerException from exc

    async def retrieve_signup_term_ids(self) -> List[int]:
        """
        신규 가입 시 필요한 약관 ID 조회
        """

        signup_term_types = [
            TermType.TERMS_OF_SERVICE,
            TermType.PRIVACY_POLICY,
            TermType.MARKETING,
        ]
        try:
            signup_terms = await self.term_repo.find_many_by_types(
                signup_term_types
            )
        except Exception as exc:
            raise DBServerException from exc

        if len(signup_terms) != len(signup_term_types) or set(
            term.type for term in signup_terms
        ) != set(signup_term_types):
            raise DataNotFoundException

        return [term.id for term in signup_terms]  # type: ignore
