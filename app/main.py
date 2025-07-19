import logging
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware

from app.core.database import init_database
from app.core.config import setting
from app.api.router import router


logging.basicConfig(level=logging.INFO, format='%(message)s')


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=setting.SESSION_MIDDLEWARE_SECRET)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=setting.APP_PORT,
        reload=True,
    )
