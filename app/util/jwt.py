from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt

from app.util.schema import Payload
from app.core.config import env


def jwt_encode(
    payload: Payload,
    expire_delta: Optional[timedelta] = timedelta(days=3),
) -> str:
    expire = datetime.now(timezone.utc) + expire_delta  # type: ignore
    iat = datetime.now(timezone.utc)

    payload_dict = payload.model_dump()
    payload_dict.update({"exp": expire, "iat": iat})

    return jwt.encode(payload_dict, env.jwt_secret, algorithm="HS256")


def jwt_decode(token: str) -> Payload:
    decoded = jwt.decode(
        token,
        env.jwt_secret,
        algorithms=["HS256"],
        options={"verify_signature": True},
    )

    return Payload(
        id=decoded["id"], name=decoded["name"], roles=decoded["roles"]
    )
