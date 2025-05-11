from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from app.core.config import env
from app.db.init import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=env.app_port,
        reload=True,
    )
