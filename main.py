from aiogram import Bot, Dispatcher
import asyncio
from bot.handlers import setup_handlers
from bot.database import init_db, delete_expired_records
from aiogram.fsm.storage.memory import MemoryStorage  # Простое хранилище
import os
from dotenv import load_dotenv

# Загрузка токена
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Укажите токен бота в .env!")

bot = Bot(token=TOKEN)
storage = MemoryStorage()  # Хранилище для FSM
dp = Dispatcher(storage=storage)

async def main():
    # Инициализация базы данных
    await init_db()

    # Удаление устаревших записей каждые 60 минут
    asyncio.create_task(periodic_cleanup())

    # Настройка обработчиков
    setup_handlers(dp)

    # Запуск бота
    await dp.start_polling(bot)

async def periodic_cleanup():
    while True:
        await delete_expired_records()
        await asyncio.sleep(3600)  # Удаляем записи каждые 60 минут

if __name__ == "__main__":
    asyncio.run(main())
