import redis
from src.config.settings import settings

def get_redis():
    r = redis.from_url(settings.redis_url)
    try:
        yield r
    finally:
        r.close()
