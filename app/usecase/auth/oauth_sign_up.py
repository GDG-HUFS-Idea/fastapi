from typing import List, Optional, cast
from fastapi import Request
from pydantic import BaseModel

from app.common.enums import SubscriptionPlan, UserRole
from app.domain.user_agreement import UserAgreement
from app.domain.user import User
from app.repository.term import TermRepository
from app.repository.user_agreement import UserAgreementRepository
from app.repository.user import UserRepository
from app.service.auth.jwt import JWTService, Payload
from app.service.cache.oauth_profile import OAuthProfileCache
from app.common.exceptions import (
    UsecaseException,
    UnauthorizedException,
    NotFoundException,
    HostMismatchException,
    InvalidTermException,
    RequiredTermNotAgreedException,
    MissingTermException,
    InternalServerException,
    RepositoryError,
    JWTError,
    CacheError,
)


class _TermAgreement(BaseModel):
    term_id: int
    is_agreed: bool


class OAuthSignUpUsecaseDTO(BaseModel):
    code: str
    term_agreements: List[_TermAgreement]


class _User(BaseModel):
    name: str
    email: str
    roles: List[UserRole]


class OAuthSignUpUsecaseResponse(BaseModel):
    token: str
    user: _User


class OAuthSignUpUsecase:

    def __init__(
        self,
        user_repository: UserRepository,
        term_repository: TermRepository,
        user_agreement_repository: UserAgreementRepository,
        oauth_profile_cache: OAuthProfileCache,
    ) -> None:
        self._user_repository = user_repository
        self._term_repository = term_repository
        self._user_agreement_repository = user_agreement_repository
        self._oauth_profile_cache = oauth_profile_cache

    async def execute(
        self,
        request: Request,
        dto: OAuthSignUpUsecaseDTO,
    ) -> OAuthSignUpUsecaseResponse:
        try:
            # 1. OAuth 프로필 조회 및 호스트 검증
            host: Optional[str] = getattr(request.client, "host", None)
            if not host:
                raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

            oauth_profile = await self._oauth_profile_cache.get(dto.code)
            if not oauth_profile:
                raise NotFoundException("OAuth 프로필을 찾을 수 없습니다")

            if oauth_profile.host != host:
                raise HostMismatchException("요청한 호스트와 OAuth 프로필의 호스트가 일치하지 않습니다")

            # 2. 활성 약관 조회 및 동의 내역 검증
            active_terms = await self._term_repository.find_active_terms()
            await self._validate_term_agreements(dto.term_agreements, active_terms)

            # 3. 신규 사용자 생성 및 저장
            user = User(
                name=oauth_profile.name,
                email=oauth_profile.email,
                roles=[UserRole.GENERAL],
                subscription_plan=SubscriptionPlan.FREE,
            )
            await self._user_repository.save(user)

            # 4. 약관 동의 내역 저장
            user_id = cast(int, user.id)
            submitted_term_agreements = [
                UserAgreement(
                    user_id=user_id,
                    term_id=agreement.term_id,
                    is_agreed=agreement.is_agreed,
                )
                for agreement in dto.term_agreements
            ]
            await self._user_agreement_repository.save_batch(submitted_term_agreements)

            # 5. JWT 토큰 생성
            token = JWTService.encode(
                payload=Payload(
                    id=user_id,
                    name=user.name,
                    roles=user.roles,
                )
            )

            # 6. OAuth 프로필 캐시 정리
            await self._oauth_profile_cache.evict(dto.code)

            # 7. 회원가입 완료 응답 반환
            return OAuthSignUpUsecaseResponse(
                token=token,
                user=_User(
                    name=user.name,
                    email=user.email,
                    roles=user.roles,
                ),
            )

        except (JWTError, RepositoryError, CacheError) as exception:
            raise InternalServerException(str(exception)) from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            raise InternalServerException(f"OAuth 회원가입 처리 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def _validate_term_agreements(self, term_agreements, active_terms):
        """약관 동의 내역 유효성 검증"""
        submitted_term_ids = {agreement.term_id for agreement in term_agreements}
        active_term_ids = {term.id for term in active_terms}

        # 유효하지 않은 약관 ID 확인
        invalid_term_ids = submitted_term_ids - active_term_ids
        if invalid_term_ids:
            raise InvalidTermException(f"유효하지 않은 약관 ID가 포함되어 있습니다: {list(invalid_term_ids)}")

        # 필수 약관 동의 여부 확인
        required_terms = [term for term in active_terms if term.is_required]
        term_agreement_map = {agreement.term_id: agreement.is_agreed for agreement in term_agreements}

        for required_term in required_terms:
            if required_term.id not in term_agreement_map:
                raise RequiredTermNotAgreedException(f"필수 약관 '{required_term.title}'에 대한 동의가 누락되었습니다")
            if not term_agreement_map[required_term.id]:
                raise RequiredTermNotAgreedException(f"필수 약관 '{required_term.title}'에 동의해야 합니다")

        # 모든 활성 약관 제출 여부 확인
        missing_term_ids = active_term_ids - submitted_term_ids
        if missing_term_ids:
            missing_terms = [term for term in active_terms if term.id in missing_term_ids]
            missing_term_titles = [term.title for term in missing_terms]
            raise MissingTermException(f"누락된 약관이 있습니다: {missing_term_titles}")
