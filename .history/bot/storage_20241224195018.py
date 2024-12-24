import aioredis
from datetime import datetime, timedelta

redis = None

async def setup_redis(url: str):
    global redis
    redis = aioredis.from_url(url, decode_responses=True)

async def add_to_waiting(user, number):
    entry_key = f"number:{number}"
    await redis.hset(entry_key, mapping={
        "number": number,
        "user": user,
        "status": "🔵 Ожидание",
        "timestamp": datetime.now().isoformat()
    })
    await redis.sadd("waiting_list", entry_key)
    await redis.expire(entry_key, 86400)  # Устанавливаем TTL на 24 часа
    return f"Номер {number} добавлен в список ожидания."

async def move_to_hold(number):
    entry_key = f"number:{number}"
    if not await redis.exists(entry_key):
        return "Номер не найден."

    await redis.hset(entry_key, mapping={
        "status": "🟠 Холдинг",
        "hold_start": datetime.now().isoformat(),
        "hold_end": (datetime.now() + timedelta(hours=3)).isoformat()
    })
    await redis.srem("waiting_list", entry_key)
    await redis.sadd("hold_list", entry_key)
    return f"Номер {number} взят в холд."

async def mark_as_successful(number):
    entry_key = f"number:{number}"
    if not await redis.exists(entry_key):
        return "Номер не найден."

    await redis.hset(entry_key, mapping={
        "status": "🟢 Успешно",
        "success_at": datetime.now().isoformat()
    })
    await redis.srem("hold_list", entry_key)
    await redis.sadd("successful_list", entry_key)
    return f"Номер {number} успешно завершил холд."

async def mark_as_failed(number):
    entry_key = f"number:{number}"
    if not await redis.exists(entry_key):
        return "Номер не найден."

    await redis.hset(entry_key, mapping={
        "status": "🔴 Слетел",
        "failed_at": datetime.now().isoformat()
    })
    await redis.srem("hold_list", entry_key)
    await redis.sadd("failed_list", entry_key)
    return f"Номер {number} помечен как слетевший."

async def clear_all():
    keys = await redis.keys("number:*")
    for key in keys:
        await redis.delete(key)

    await redis.delete("waiting_list")
    await redis.delete("hold_list")
    await redis.delete("successful_list")
    await redis.delete("failed_list")
