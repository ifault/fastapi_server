import os

import redis as rr
from dotenv import load_dotenv

load_dotenv()
_redis_client = None


def get_redis_client():
    global _redis_client
    r_host = os.getenv("REDIS_HOST")
    r_port = os.getenv("REDIS_PORT")
    if _redis_client is None:
        _redis_client = rr.from_url(f"redis://{r_host}:{r_port}", db=2, decode_responses=True)
    return _redis_client
