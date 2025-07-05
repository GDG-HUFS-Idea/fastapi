# RepositoryError
from fastapi import HTTPException


class RepositoryError(Exception):  # 모든 Repository 예외의 기본 클래스
    pass


class DatabaseConnectionError(RepositoryError):  # 데이터베이스 연결/트랜잭션 오류
    pass


class UserRepositoryError(RepositoryError):  # User 관련 모든 오류
    pass


class TermRepositoryError(RepositoryError):  # Term 관련 모든 오류
    pass


class UserAgreementRepositoryError(RepositoryError):  # UserAgreement 관련 모든 오류
    pass


# CacheError
class CacheError(Exception):  # Cache 관련 모든 오류의 기본 클래스
    pass


class CacheConnectionError(CacheError):  # Redis 연결 오류
    pass


class CacheKeyGenerationError(CacheError):  # 키 생성 실패
    pass


class CacheDataCorruptedError(CacheError):  # 캐시 데이터 손상
    pass


class CacheSerializationError(CacheError):  # 직렬화/역직렬화 오류
    pass


# AuthenticationError
class AuthError(Exception):  # 모든 인증 오류의 기본 클래스
    pass


class JWTError(AuthError):  # JWT 관련 모든 오류
    pass


class JWTEncodeError(JWTError):  # JWT 토큰 생성 실패
    pass


class JWTDecodeError(JWTError):  # JWT 토큰 파싱 실패
    pass


class JWTExpiredError(JWTError):  # JWT 토큰 만료
    pass


class JWTInvalidError(JWTError):  # JWT 토큰 무효
    pass


class OAuthError(AuthError):  # OAuth 관련 모든 오류
    pass


class OAuthRedirectError(OAuthError):  # OAuth 리다이렉트 실패
    pass


class OAuthStateError(OAuthError):  # OAuth 상태 불일치
    pass


class OAuthProfileError(OAuthError):  # OAuth 프로필 조회 실패
    pass


class OAuthDataCorruptedError(OAuthError):  # OAuth 응답 데이터 손상
    pass


# AnalyzerError
class AnalysisServiceError(Exception):  # 모든 분석 서비스 오류의 기본 클래스
    pass


class ExternalAPIError(AnalysisServiceError):  # 외부 API 호출 오류
    pass


class JSONValidationError(ValueError, AnalysisServiceError):  # JSON 형식 검증 오류
    pass


class ModelValidationError(AnalysisServiceError):  # Pydantic 모델 검증 오류
    pass


class PromptGenerationError(AnalysisServiceError):  # 프롬프트 생성 오류
    pass


# UsecaseError
class UsecaseException(HTTPException):  # 모든 Usecase 오류의 기본 클래스
    def __init__(self, detail: str, status_code: int = 500):
        super().__init__(status_code=status_code, detail=detail)


class InvalidInputException(UsecaseException):  # 잘못된 입력 데이터
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=400)


class UnauthorizedException(UsecaseException):  # 인증 실패
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=401)


class ForbiddenException(UsecaseException):  # 권한 없음
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=403)


class NotFoundException(UsecaseException):  # 리소스를 찾을 수 없음
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=404)


class BusinessLogicException(UsecaseException):  # 비즈니스 로직 오류
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=422)


class InternalServerException(UsecaseException):  # 내부 서버 오류
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=500)


class HostMismatchException(ForbiddenException):  # 호스트 불일치
    pass


class RequiredTermNotAgreedException(BusinessLogicException):  # 필수 약관 미동의
    pass


class InvalidTermException(BusinessLogicException):  # 유효하지 않은 약관
    pass


class MissingTermException(BusinessLogicException):  # 누락된 약관
    pass
