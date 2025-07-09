from typing import Optional


class Base(Exception):
    def __init__(self, name: Optional[str] = None, headers=None):
        self.name = name if name is not None else self.name
        self.headers = headers
        super().__init__(self.name)


class FieldMissingException(Base):
    status = 400
    name = "필수 필드 누락"


class ValidationException(Base):
    status = 422
    name = "데이터 유효성 검증 실패"


class NoPermissionException(Base):
    status = 403
    name = "권한 없음"


class DataNotFoundException(Base):
    status = 404
    name = "제공할 데이터 없음"


class CSRFException(Base):
    status = 403
    name = "CSRF 토큰 불일치"


class DBServerException(Base):
    status = 502
    name = "DB 서버 오류"


class OAuthServerException(Base):
    status = 502
    name = "OAuth 서버 연결 오류"


class CacheServerException(Base):
    status = 502
    name = "캐시 서버 오류"
