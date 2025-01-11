# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
import os
from dotenv import load_dotenv
import logging
from bot.utils import set_redis
from bot.handlers import setup_handlers
from bot.database import init_db, delete_expired_records

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"

if not TOKEN:
    raise ValueError("Set your bot token in .env!")

redis = Redis.from_url(REDIS_URL)
set_redis(redis)
storage = RedisStorage(redis)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

async def main():
    await init_db()

    # Start background task for periodic cleanup
    asyncio.create_task(delete_expired_records())

    setup_handlers(dp)

    logger.info("Bot started!")
    await dp.start_polling(bot)

async def delete_expired_records():
    while True:
        try:
            await init_db.delete_expired_records()
            logger.info("Cleanup of expired records completed.")
        except Exception as e:
            logger.error(f"Database cleanup error: {e}")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())