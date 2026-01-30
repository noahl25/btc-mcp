import redis.asyncio as redis

redis = r = redis.Redis(host="localhost", port=9000, db=0, decode_responses=True)