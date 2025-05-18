from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request, Response
from starlette.middleware.sessions import SessionMiddleware
from fastapi.exceptions import (
    RequestValidationError as RequestValidationException,
)
from starlette.exceptions import HTTPException

from app.core.config import env
from app.db.init import init_db
from app.api.router.auth import auth_router
from app.core.config import env
from app.util.exception import FieldMissingException, ValidationException


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=env.session_middleware_secret)

app.include_router(auth_router)


@app.exception_handler(RequestValidationException)
def validation_exception_handler(
    req: Request, exc: RequestValidationException
) -> Response:
    """
    pydantic의 BaseModel(DTO)에서 발생하는 RequestValidationException를 처리하여
    다시금 global exception handler로 전달하는 핸들러
    """
    exc_type = exc.errors()[0].get("type", "")

    if "missing" in exc_type:
        raise FieldMissingException from exc
    else:
        raise ValidationException from exc


@app.exception_handler(HTTPException)
def global_http_exception_handler(req: Request, exc: HTTPException):
    """
    FastAPI 자체에서 발생하는 모든 HTTP 예외를 처리하는 핸들러
    """

    return Response(status_code=exc.status_code, headers=exc.headers)


@app.exception_handler(Exception)
def global_exception_handler(req: Request, exc: Exception):
    """
    모든 예외를 처리하는 핸들러
    """
    status = getattr(exc, "status", 500)
    headers = getattr(exc, "headers", None)

    res = Response(status_code=status)

    if headers:
        for name, value in headers.items():
            res.headers[name] = value

    return res


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=env.app_port,
        reload=True,
    )
