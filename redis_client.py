# redis_client.py
import redis
from config import REDIS_HOST, REDIS_PORT
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:     %(message)s')

# Create a redis client with url
logging.info(f"Creating a redis client: {REDIS_HOST}:{REDIS_PORT}")
client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
logging.info("Redis client created successfully!")