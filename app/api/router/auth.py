from typing import Annotated
from fastapi import APIRouter, Depends, Request

from app.service.auth.redirect_oauth import (
    RedirectOAuthService,
    RedirectOAuthServiceDTO,
)


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get(path="/oauth/{provider}")
async def redirect_oauth(
    req: Request,
    dto: Annotated[RedirectOAuthServiceDTO, Depends()],
    service=RedirectOAuthService(),
):
    return await service.exec(req, dto)


@auth_router.get(
    path="/oauth/{provider}/callback",
    name="handle_oauth_callback",
)
async def handle_oauth_callback(
    req: Request,
):
    return
