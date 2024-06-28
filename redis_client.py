import redis as rr
_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = rr.Redis(host='host.docker.internal', port=6379, db=2)
    return _redis_client
