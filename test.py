import asyncio
from redis.asyncio import Redis

async def test_redis():
    redis = Redis(host="localhost", port=6379, decode_responses=True)
    await redis.set("test_key", "hello_redis")
    value = await redis.get("test_key")
    print(f"Полученное значение: {value}")  # Ожидается: hello_redis
    await redis.aclose()  # Используем aclose вместо close

asyncio.run(test_redis())
