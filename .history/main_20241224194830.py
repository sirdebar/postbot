from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
from bot.handlers import setup_handlers
from bot.storage import clear_storage
import os
from dotenv import load_dotenv

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Укажите токен бота в .env!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    # Устанавливаем обработчики
    setup_handlers(dp)
    dp.startup.register(clear_storage)  # Регистрация очистки хранилища

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
