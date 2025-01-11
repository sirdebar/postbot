import asyncio
from aiogram import Bot, Dispatcher
from bot.handlers import setup_handlers
from bot.database import init_db, delete_expired_records
from aiogram.fsm.storage.redis import RedisStorage
import os
from dotenv import load_dotenv
import logging
from redis.asyncio import Redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"

if not TOKEN:
    raise ValueError("Set your bot token in .env!")

bot = Bot(token=TOKEN)
redis = Redis.from_url(REDIS_URL)
storage = RedisStorage(redis)
dp = Dispatcher(storage=storage)

async def main():
    await init_db()

    # Start background task for periodic cleanup
    asyncio.create_task(periodic_cleanup())

    setup_handlers(dp, redis)

    logger.info("Bot started!")
    await dp.start_polling(bot)

async def periodic_cleanup():
    while True:
        try:
            await delete_expired_records()
            logger.info("Cleanup of expired records completed.")
        except Exception as e:
            logger.error(f"Database cleanup error: {e}")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())