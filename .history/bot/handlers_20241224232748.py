from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Text
from bot.database import (
    add_to_waiting, update_status, get_records_by_status, get_all_records, clear_all, format_list, count_records
)
from bot.utils import format_records, build_pagination_keyboard
from datetime import datetime, timedelta

def setup_handlers(dp: Dispatcher):
    dp.message.register(add_number_handler, Command(commands=["a"]))
    dp.message.register(list_all_handler, Command(commands=["l"]))
    dp.message.register(get_waiting_handler, Command(commands=["wl"]))
    dp.message.register(get_hold_handler, Command(commands=["hl"]))
    dp.message.register(get_successful_handler, Command(commands=["gl"]))
    dp.message.register(get_failed_handler, Command(commands=["sl"]))
    dp.message.register(hold_number_handler, Command(commands=["c"]))
    dp.message.register(mark_failed_handler, Command(commands=["s"]))
    dp.message.register(clear_all_handler, Command(commands=["clear"]))
    dp.message.register(help_handler, Command(commands=["help"]))
    dp.callback_query.register(paginate_list, Text(startswith="page:"))
    dp.callback_query.register(paginate_list, lambda c: c.data.startswith("page:"))

async def add_number_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /a 123456789")
        return

    number = args[1]
    user_name = message.from_user.full_name or "Без имени"
    response = await add_to_waiting(user_name, number)
    await message.reply(response)

async def list_all_handler(message: Message):
    """
    Выводит первую страницу общего списка.
    """
    limit = 20
    offset = 0
    current_page = 1

    total_records = await count_records()
    total_pages = (total_records + limit - 1) // limit
    records = await get_all_records(limit=limit, offset=offset)

    response = format_list(records, f"Общий список (стр. {current_page}/{total_pages})")
    keyboard = build_pagination_keyboard(current_page, total_pages)

    await message.reply(response, reply_markup=keyboard, parse_mode="Markdown")


async def get_waiting_handler(message: Message):
    records = await get_records_by_status("🔵 Ожидание")
    response, keyboard = format_records(records, "Ожидание")
    await message.reply(response, reply_markup=keyboard)

async def get_hold_handler(message: Message):
    records = await get_records_by_status("🟠 Холдинг")
    response, keyboard = format_records(records, "Холдинг")
    await message.reply(response, reply_markup=keyboard)

async def get_successful_handler(message: Message):
    records = await get_records_by_status("🟢 Успешно")
    response, keyboard = format_records(records, "Успешно")
    await message.reply(response, reply_markup=keyboard)

async def get_failed_handler(message: Message):
    records = await get_records_by_status("🔴 Слетел")
    response, keyboard = format_records(records, "Слетевшие")
    await message.reply(response, reply_markup=keyboard)

async def hold_number_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /c 123456789")
        return

    number = args[1]
    hold_start = datetime.now()
    hold_end = hold_start + timedelta(hours=3)
    await update_status(number, "🟠 Холдинг", hold_start, hold_end)
    await message.reply(f"Номер {number} взят в холд.")

async def mark_failed_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /s 123456789")
        return

    number = args[1]
    await update_status(number, "🔴 Слетел")
    await message.reply(f"Номер {number} помечен как слетевший.")

async def clear_all_handler(message: Message):
    response = await clear_all()
    await message.reply(response)

async def help_handler(message: Message):
    help_text = (
        "/a {номер} — Добавить номер в ожидание.\n"
        "/c {номер} — Взять номер в холд.\n"
        "/success {номер} — Пометить номер как успешный.\n"
        "/s {номер} — Пометить номер как слетевший.\n"
        "/clear — Очистить все списки.\n"
        "/l — Общий список.\n"
        "/wl — Показать список ожидания.\n"
        "/hl — Показать список холда.\n"
        "/gl — Показать успешные номера.\n"
        "/sl — Показать слетевшие номера."
    )
    await message.reply(help_text)

async def paginate_list(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    offset = (page - 1) * 20
    records = await get_all_records(limit=20, offset=offset)
    response, keyboard = format_records(records, f"Общий список (стр. {page})")
    await callback.message.edit_text(response, reply_markup=keyboard)
