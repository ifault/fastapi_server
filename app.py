import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise

from app_redis import get_redis
from routes import api
from settings import TORTOISE_ORM
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)


@asynccontextmanager
async def lifespan(fapp: FastAPI):
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    fapp.redis = await get_redis()
    yield
    await fapp.redis.close()
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST"), port=8000)
