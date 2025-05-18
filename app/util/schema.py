from pydantic import BaseModel


class RawProfile(BaseModel):
    name: str
    email: str


class OAuthProfile(BaseModel):
    email: str
    name: str
    host: str
