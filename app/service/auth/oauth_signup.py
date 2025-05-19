from datetime import timedelta
from typing import List
from fastapi import Request
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from app.cache.oauth_profile import OAuthProfileCache
from app.db.model.term import Term
from app.db.model.term_agreement import TermAgreement
from app.db.model.user import User
from app.repo.term import TermRepo
from app.repo.term_agreement import TermAgreementRepo
from app.repo.user import UserRepo
from app.util.enum import PlanType, TermType, UserRole
from app.util.exception import (
    CacheServerException,
    DBServerException,
    DataNotFoundException,
    FieldMissingException,
    NoPermissionException,
    ValidationException,
)
from app.util.jwt import jwt_encode
from app.util.schema import OAuthProfile, Payload


class TermAgreementDTO(BaseModel):
    term_id: int
    has_agreed: bool


class OAuthSignupServiceDTO(BaseModel):
    code: str
    term_agreements: List[TermAgreementDTO]


class OAuthSignupServiceResponse(BaseModel):
    token: str
    user_id: int
    roles: List[UserRole]
    name: str


class OAuthSignupService:

    def __init__(self, pg_session: AsyncSession, redis_session: Redis):
        self.user_repo = UserRepo(pg_session)
        self.term_repo = TermRepo(pg_session)
        self.term_agreement_repo = TermAgreementRepo(pg_session)
        self.oauth_profile_cache = OAuthProfileCache(redis_session)

    async def exec(
        self, req: Request, dto: OAuthSignupServiceDTO
    ) -> OAuthSignupServiceResponse:
        host = self.extract_host(req)
        profile = await self.get_oauth_profile(dto.code, host)
        signup_terms = await self.retrieve_signup_terms()

        self.validate_agreements(signup_terms, dto.term_agreements)

        user = await self.save_user(profile)
        await self.save_term_agreements(user.id, dto.term_agreements)  # type: ignore

        token = self.sign_token(user)
        await self.evict_oauth_profile(dto.code)

        return OAuthSignupServiceResponse(
            token=token,
            user_id=user.id,  # type: ignore
            roles=user.roles,
            name=user.name,
        )

    def extract_host(self, req: Request) -> str:
        """
        요청에서 host 추출
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
            profile = await self.oauth_profile_cache.get(id)
        except Exception as exc:
            raise CacheServerException from exc

        if not profile:
            raise DataNotFoundException
        elif profile.host != host:
            raise NoPermissionException

        return profile

    async def retrieve_signup_terms(self) -> List[Term]:
        """
        약관 동의 목록 조회
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

        if (len(signup_terms) != len(signup_term_types)) or set(
            term.type for term in signup_terms
        ) != set(signup_term_types):
            raise DataNotFoundException

        return signup_terms

    def validate_agreements(
        self,
        signup_terms: List[Term],
        dto_term_agreements: List[TermAgreementDTO],
    ) -> None:
        """
        사용자가 제출한 약관 동의가 유효한지 검증
        (필수 약관 동의 검사...등)
        """

        signup_term_ids: set[int] = {term.id for term in signup_terms}  # type: ignore
        dto_term_ids = {term.term_id for term in dto_term_agreements}

        if signup_term_ids != dto_term_ids:
            raise ValidationException

        required_term_ids: set[int] = {term.id for term in signup_terms if term.is_required}  # type: ignore
        agreed_term_ids = {
            term.term_id for term in dto_term_agreements if term.has_agreed
        }

        if not required_term_ids.issubset(agreed_term_ids):
            raise FieldMissingException

    async def save_user(self, profile: OAuthProfile) -> User:
        """
        해당 OAuth profile 정보로 신규 사용자 생성
        """

        user = User(
            name=profile.name,
            email=profile.email,
            roles=[UserRole.GENERAL],
            plan=PlanType.FREE,
        )
        try:
            await self.user_repo.save(user)
        except Exception as exc:
            raise DBServerException from exc

        return user

    async def save_term_agreements(
        self, user_id: int, dto_agreements: List[TermAgreementDTO]
    ) -> None:
        """
        사용자가 동의한 약관 정보 저장
        """

        term_agreements = [
            TermAgreement(
                user_id=user_id,
                term_id=term_agreement.term_id,
                has_agreed=term_agreement.has_agreed,
            )
            for term_agreement in dto_agreements
        ]

        try:
            await self.term_agreement_repo.save_many(term_agreements)
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
        try:
            return await self.oauth_profile_cache.evict(id)
        except Exception as exc:
            raise CacheServerException from exc
