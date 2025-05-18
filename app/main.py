from contextlib import asynccontextmanager
from pydantic import ValidationError
import uvicorn
from fastapi import FastAPI, Request, Response
from starlette.middleware.sessions import SessionMiddleware

from fastapi.exceptions import RequestValidationError
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


@app.exception_handler(RequestValidationError)
def request_validation_exception_handler(
    req: Request, exc: RequestValidationError
) -> Response:
    """
    FastAPI 요청 파라미터 검증 실패 시 발생하는 예외를 처리하는 핸들러
    """

    exc_type = exc.errors()[0].get("type", "")

    if "missing" in exc_type:
        raise FieldMissingException from exc
    else:
        raise ValidationException from exc


@app.exception_handler(ValidationError)
def validation_exception_handler(
    req: Request, exc: ValidationError
) -> Response:
    """
    Pydantic 모델(DTO) 검증 실패 시 발생하는 예외를 ValidationException으로 변환하는 핸들러.
    """
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
    print(f"Exception caught in global handler: {type(exc).__name__}")
    print(f"Exception details: {str(exc)}")

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
