import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise

from app_redis import get_redis
from routes import server, api, demo
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



@app.get("/status/{task_id}")
async def get_worker_status(task_id: str):
    task = start_get_ticket.AsyncResult(task_id)
    return task.result

app.include_router(server.ws_router, prefix="/ws")
app.include_router(api.router, prefix="/api")
app.include_router(demo.demo_router, prefix="/demo")



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST"), port=8000)
