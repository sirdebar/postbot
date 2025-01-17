import asyncio
from aiogram import Bot, Dispatcher
from bot.handlers import setup_handlers
from bot.database import init_db, delete_expired_records
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
import os
from dotenv import load_dotenv
import logging
from bot.database import (
    mark_as_successful, get_pool
)
from datetime import datetime, timezone, timedelta

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"

if not TOKEN:
    raise ValueError("Set your bot token in .env!")

redis = Redis.from_url(REDIS_URL)
storage = RedisStorage(redis)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

async def periodic_cleanup():
    while True:
        try:
            from bot.database import delete_expired_records  # Импортируем функцию из database.py
            await delete_expired_records()
            logger.info("Cleanup of expired records completed.")
        except Exception as e:
            logger.error(f"Database cleanup error: {e}")
        await asyncio.sleep(3600)

async def check_holds():
    while True:
        try:
            hold_duration_str = await redis.get("global_hold_duration")
            if hold_duration_str:
                hold_duration = int(hold_duration_str)
            else:
                hold_duration = None
            now = datetime.now(timezone.utc)
            pool = await get_pool()
            async with pool.acquire() as conn:
                if hold_duration:
                    records = await conn.fetch("""
                        SELECT id, number, hold_set_by, chat_id
                        FROM numbers
                        WHERE status = '🟠 Холдинг'
                        AND hold_start + hold_duration <= $1
                    """, now)
                else:
                    records = await conn.fetch("""
                        SELECT id, number, hold_set_by, chat_id
                        FROM numbers
                        WHERE status = '🟠 Холдинг'
                        AND hold_start IS NOT NULL
                    """)
                for record in records:
                    await mark_as_successful(record['number'], record['chat_id'], bot)
        except Exception as e:
            logger.error(f"Error checking holds: {e}")
        await asyncio.sleep(60)  # Check every minute

async def main():
    await init_db()
    asyncio.create_task(periodic_cleanup())
    asyncio.create_task(check_holds())
    setup_handlers(dp, redis)
    logger.info("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())