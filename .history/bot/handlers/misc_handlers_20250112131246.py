# handlers/misc_handlers.py
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from bot.database import count_records

async def help_handler(message: Message):
    if await is_admin(message.from_user.id):
        help_text = (
            "/a {номер} — Добавить номер в ожидание.\n"
            "/c {номер} — Взять номер в холд.\n"
            "/success {номер} — Пометить номер как успешный.\n"
            "/s {номер} — Пометить номер как слетевший.\n"
            "/clear — Очистить все списки.\n"
            "/wl — Показать список ожидания.\n"
            "/hl — Показать список холда.\n"
            "/gl — Показать успешные номера.\n"
            "/sl — Показать слетевшие номера.\n"
            "/search — Найти номер.\n"
            "/admin {user_id} — Назначить админа.\n"
            "/deladmin {user_id} — Удалить админа.\n"
            "/my — Показать свою статистику.\n"
            "/my {user_id} — Показать статистику другого пользователя.\n"
            "/stata — Показать полную статистику (только для админов).\n"
            "/h {hours} — Установить время холда.\n"
            "/aa {номер} — Удалить номер из списка ожидания."
        )
    else:
        help_text = (
            "/a {номер} — Добавить номер в ожидание.\n"
            "/wl — Показать список ожидания.\n"
            "/hl — Показать список холда.\n"
            "/gl — Показать успешные номера.\n"
            "/sl — Показать слетевшие номера.\n"
            "/search — Найти номер.\n"
            "/my — Показать свою статистику.\n"
        )
    await message.reply(help_text)

async def stata_handler(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    waiting = await count_records(status="🔵 Ожидание")
    holding = await count_records(status="🟠 Холдинг")
    successful = await count_records(status="🟢 Успешно")
    failed = await count_records(status="🔴 Слетел")
    response = (
        f"Полная статистика:\n\n"
        f"Ожидание: {waiting}\n"
        f"Холд: {holding}\n"
        f"Успешные: {successful}\n"
        f"Слетевшие: {failed}"
    )
    await message.reply(response)

def register_misc_handlers(dp: Dispatcher, redis_instance):
    dp.message.register(help_handler, Command(commands=["help"]))
    dp.message.register(stata_handler, Command(commands=["stata"]))