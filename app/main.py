from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import env
from app.db.init import init_db
from app.api.router.auth import auth_router
from app.core.config import env


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=env.session_middleware_secret)

app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=env.app_port,
        reload=True,
    )
