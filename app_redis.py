import os

import redis.asyncio as redis
from dotenv import load_dotenv
load_dotenv()


async def init_redis_pool() -> redis.Redis:
    r_host = os.getenv("REDIS_HOST")
    r_port = os.getenv("REDIS_PORT")
    redis_c = await redis.from_url(
        f'redis://{r_host}:{r_port}',
        encoding="utf-8",
        db=2,
        decode_responses=True,
    )
    return redis_c
