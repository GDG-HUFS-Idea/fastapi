from datetime import timedelta
from typing import List, Optional, cast
from fastapi import Query, Request
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import UserRole
from app.domain.user import User
from app.repository.term import TermRepository
from app.repository.user import UserRepository
from app.service.auth.jwt import JWTService, Payload
from app.service.cache.oauth_profile import OAuthProfile, OAuthProfileCache
from app.common.exceptions import (
    UsecaseException,
    UnauthorizedException,
    NotFoundException,
    HostMismatchException,
    BusinessLogicException,
    InternalServerException,
    RepositoryError,
    JWTError,
    CacheError,
)


class RetrieveOAuthResultUsecaseDTO(BaseModel):
    code: str = Field(Query(min_length=10, max_length=100, description="OAuth 제공자로부터 받은 authorization code"))

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "code": "wnm_utANhykZXmAEbqTbrg",
                }
            ]
        }
    )


class RetrieveOAuthResultUsecaseResponse(BaseModel):
    has_account: bool = Field(description="사용자 계정 존재 여부")

    token: Optional[str] = Field(default=None, description="JWT 토큰 (계정이 있는 경우)")
    user_id: Optional[int] = Field(default=None, description="사용자 ID (계정이 있는 경우)")
    name: Optional[str] = Field(default=None, description="사용자 이름 (계정이 있는 경우)")
    roles: Optional[List[UserRole]] = Field(default=None, description="사용자 역할 목록 (계정이 있는 경우)")

    code: Optional[str] = Field(default=None, description="임시 코드 (계정이 없는 경우)")
    active_term_ids: Optional[List[int]] = Field(default=None, description="활성화된 약관 ID 목록 (계정이 없는 경우)")


class RetrieveOAuthResultUsecase:
    _TOKEN_EXPIRE_DELTA = timedelta(days=3)
    _UNTIL_TERM_AGREEMENT_EXPIRE_DELTA = timedelta(minutes=15)

    def __init__(
        self,
        user_repository: UserRepository,
        term_repository: TermRepository,
        oauth_profile_cache: OAuthProfileCache,
    ) -> None:
        self._user_repository = user_repository
        self._term_repository = term_repository
        self._oauth_profile_cache = oauth_profile_cache

    async def execute(
        self,
        request: Request,
        dto: RetrieveOAuthResultUsecaseDTO,
    ) -> RetrieveOAuthResultUsecaseResponse:
        try:
            # 1. 호스트 정보 및 OAuth 프로필 검증
            host: Optional[str] = getattr(request.client, "host", None)
            if not host:
                raise UnauthorizedException("클라이언트 호스트 정보를 조회할 수 없습니다")

            oauth_profile = await self._oauth_profile_cache.get(dto.code)
            if not oauth_profile:
                raise NotFoundException("OAuth 프로필을 찾을 수 없습니다")

            if oauth_profile.host != host:
                raise HostMismatchException("요청한 호스트와 OAuth 프로필의 호스트가 일치하지 않습니다")

            # 2. 기존 계정 존재 여부 확인
            user = await self._user_repository.find_by_email(oauth_profile.email)
            has_account = bool(user)

            # 3. 계정 상태에 따른 분기 처리
            if has_account:
                return await self._handle_existing_user_login(dto, user)
            else:
                return await self._handle_new_user_signup_preparation(dto, oauth_profile)

        except (CacheError, RepositoryError, JWTError) as exception:
            raise InternalServerException(str(exception)) from exception
        except UsecaseException:
            raise  # Usecase 예외는 그대로 전파
        except Exception as exception:
            raise InternalServerException(f"OAuth 결과 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def _handle_existing_user_login(
        self,
        dto: RetrieveOAuthResultUsecaseDTO,
        user: User,
    ) -> RetrieveOAuthResultUsecaseResponse:
        # JWT 토큰 생성
        token = JWTService.encode(
            payload=Payload(
                id=cast(int, user.id),
                name=user.name,
                roles=user.roles,
            ),
            expire_delta=self._TOKEN_EXPIRE_DELTA,
        )

        # OAuth 프로필 캐시 정리
        await self._oauth_profile_cache.evict(dto.code)

        return RetrieveOAuthResultUsecaseResponse(
            has_account=True,
            token=token,
            user_id=user.id,
            roles=user.roles,
            name=user.name,
        )

    async def _handle_new_user_signup_preparation(
        self,
        dto: RetrieveOAuthResultUsecaseDTO,
        oauth_profile: OAuthProfile,
    ) -> RetrieveOAuthResultUsecaseResponse:
        # OAuth 프로필을 새로운 키로 재저장
        key = await self._oauth_profile_cache.set(
            data=oauth_profile,
            expire_delta=self._UNTIL_TERM_AGREEMENT_EXPIRE_DELTA,
        )

        # 활성 약관 목록 조회
        active_terms = await self._term_repository.find_active_terms()
        if len(active_terms) == 0:
            raise BusinessLogicException("회원가입에 필요한 약관이 존재하지 않습니다")

        # 기존 OAuth 프로필 캐시 정리
        await self._oauth_profile_cache.evict(dto.code)

        active_term_ids = [cast(int, term.id) for term in active_terms]
        return RetrieveOAuthResultUsecaseResponse(
            has_account=False,
            code=key,
            active_term_ids=active_term_ids,
        )
