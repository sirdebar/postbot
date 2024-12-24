from aiogram import Bot, Dispatcher
import asyncio
from bot.handlers import setup_handlers
from bot.storage import setup_redis
import os
from dotenv import load_dotenv

# Загрузка конфигурации
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

if not TOKEN:
    raise ValueError("Укажите токен бота в .env!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    # Настраиваем Redis
    await setup_redis(REDIS_URL)

    # Устанавливаем обработчики
    setup_handlers(dp)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
