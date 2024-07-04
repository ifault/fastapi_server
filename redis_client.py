import redis as rr
_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = rr.from_url("redis://host.docker.internal:6379", db=2, decode_responses=True)
    return _redis_client
