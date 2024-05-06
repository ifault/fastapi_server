import aioredis
import redis

_redis = None


async def get_redis():
    return await aioredis.from_url("redis://redis",
                                   encoding="utf-8",
                                   decode_responses=True,
                                   db=0)


def get_redis_():
    global _redis
    if _redis is None:
        _redis = redis.Redis(host='redis', port=6379, db=0)
    return _redis
