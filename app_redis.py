import redis.asyncio as redis
from dotenv import load_dotenv
load_dotenv()


async def init_redis_pool() -> redis.Redis:
    redis_c = await redis.from_url(
        "redis://host.docker.internal:6379",
        encoding="utf-8",
        db=2,
        decode_responses=True,
    )
    return redis_c
