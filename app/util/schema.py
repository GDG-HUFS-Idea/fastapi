from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.util.enum import UserRole


class RawProfile(BaseModel):
    name: str
    email: str


class OAuthProfile(BaseModel):
    email: str
    name: str
    host: str


class Payload(BaseModel):
    id: int
    name: str
    roles: List[UserRole]
