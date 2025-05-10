import os
import redis

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# Test connection
try:
    redis_client.ping()
    print('Redis connection success')
except redis.exceptions.ConnectionError as e:
    print('Redis connection error', e)
    exit(1)