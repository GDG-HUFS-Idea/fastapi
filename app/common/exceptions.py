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
