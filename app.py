import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from tortoise import Tortoise
from tasks.morning import start_progress
from app_redis import init_redis_pool
from routes import api
from settings import TORTOISE_ORM
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

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
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/sse")
async def sse(req: Request):
    redis = await init_redis_pool()
    async def stream_generator():
        while True:
            if await req.is_disconnected():
                print("is_disconnected")
                await redis.delete("progress")
                break
            item = await redis.blpop("progress", timeout=0)
            if item:
                yield f"{item[1]}"
            # await asyncio.sleep(0.5)

    return EventSourceResponse(stream_generator())


app.include_router(api.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST"), port=8000)
