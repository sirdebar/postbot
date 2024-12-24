from aiogram import Bot, Dispatcher
import asyncio
from bot.handlers import setup_handlers
from bot.database import init_db
import os
from dotenv import load_dotenv

# Загрузка конфигурации
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Укажите токен бота в .env!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    # Инициализация базы данных
    await init_db()

    # Установка обработчиков
    setup_handlers(dp)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
