from typing import Optional


class Base(Exception):
    def __init__(self, name: Optional[str] = None, headers=None):
        self.name = name if name is not None else self.name
        self.headers = headers
        super().__init__(self.name)


class OAuthServerException(Base):
    status = 502
    name = "OAuth 서버 연결 오류"
