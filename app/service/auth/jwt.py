from datetime import datetime, timedelta, timezone
from typing import List
from jose import ExpiredSignatureError, JWTError as JoseJWTError, jwt
from pydantic import BaseModel, ValidationError

from app.core.config import setting
from app.common.enums import UserRole
from app.common.exceptions import JWTEncodeError, JWTDecodeError, JWTExpiredError, JWTInvalidError


class Payload(BaseModel):
    id: int
    name: str
    roles: List[UserRole]


class JWTService:
    _EXPIRE_DAY = 3
    _ALGORITHM = "HS256"

    @staticmethod
    def encode(
        payload: Payload,
        expire_delta: timedelta = timedelta(days=_EXPIRE_DAY),
    ) -> str:
        try:
            now = datetime.now(timezone.utc)
            expire_time = now + expire_delta

            payload_dict = payload.model_dump()
            payload_dict.update(
                {
                    "exp": expire_time,
                    "iat": now,
                }
            )

            return jwt.encode(
                payload_dict,
                setting.JWT_SECRET,
                algorithm=JWTService._ALGORITHM,
            )

        except Exception as exception:
            raise JWTEncodeError(f"JWT 토큰 생성 중 오류가 발생했습니다: {str(exception)}") from exception

    @staticmethod
    def decode(
        token: str,
    ) -> Payload:
        try:
            raw_payload = jwt.decode(
                token,
                setting.JWT_SECRET,
                algorithms=[JWTService._ALGORITHM],
                options={"verify_signature": True},
            )

            # Payload 모델에 정의된 필드만 추출
            payload_data = {key: value for key, value in raw_payload.items() if key in Payload.model_fields}

            return Payload.model_validate(payload_data)

        except ExpiredSignatureError as exception:
            raise JWTExpiredError("JWT 토큰이 만료되었습니다") from exception
        except JoseJWTError as exception:
            raise JWTInvalidError(f"JWT 토큰이 유효하지 않습니다: {str(exception)}") from exception
        except ValidationError as exception:
            raise JWTDecodeError(f"JWT 페이로드 데이터가 올바르지 않습니다: {str(exception)}") from exception
        except Exception as exception:
            raise JWTDecodeError(f"JWT 토큰 검증 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
