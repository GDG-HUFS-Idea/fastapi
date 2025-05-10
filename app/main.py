import os
import uvicorn
from fastapi import FastAPI


app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT", 80)),
        reload=True,
    )
