# redis_client.py
import redis
from config import REDIS_HOST, REDIS_PORT

# Create a redis client with url
client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
