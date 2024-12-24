from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from bot.database import (
    add_to_waiting, move_to_hold, mark_as_successful, mark_as_failed, clear_all, get_list_by_status
)
from bot.utils import format_list

def setup_handlers(dp: Dispatcher):
    dp.message.register(add_number_handler, Command(commands=["a"]))
    dp.message.register(hold_number_handler, Command(commands=["c"]))
    dp.message.register(successful_number_handler, Command(commands=["success"]))
    dp.message.register(failed_number_handler, Command(commands=["s"]))
    dp.message.register(clear_all_handler, Command(commands=["clear"]))
    dp.message.register(get_waiting_list, Command(commands=["wl"]))
    dp.message.register(get_hold_list, Command(commands=["hl"]))
    dp.message.register(get_successful_list, Command(commands=["gl"]))
    dp.message.register(get_failed_list, Command(commands=["sl"]))
    dp.message.register(help_handler, Command(commands=["help"]))

async def add_number_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /a 123456789")
        return

    number = args[1]
    user_name = message.from_user.full_name or "Без имени"
    response = await add_to_waiting(user_name, number)
    await message.reply(response)

async def hold_number_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /c 123456789")
        return

    number = args[1]
    response = await move_to_hold(number)
    await message.reply(response)

async def successful_number_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /success 123456789")
        return

    number = args[1]
    response = await mark_as_successful(number)
    await message.reply(response)

async def failed_number_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /s 123456789")
        return

    number = args[1]
    response = await mark_as_failed(number)
    await message.reply(response)

async def clear_all_handler(message: Message):
    response = await clear_all()
    await message.reply(response)

async def list_all_handler(message: Message):
    records = await get_all_records()
    response = format_list(records, "Общий список всех номеров")
    await message.reply(response, parse_mode="Markdown")

async def get_waiting_list(message: Message):
    records = await get_list_by_status("🔵 Ожидание")
    response = format_list(records, "Ожидание")
    await message.reply(response)

async def get_hold_list(message: Message):
    records = await get_list_by_status("🟠 Холдинг")
    response = format_list(records, "Холдинг")
    await message.reply(response)

async def get_successful_list(message: Message):
    records = await get_list_by_status("🟢 Успешно")
    response = format_list(records, "Успешно")
    await message.reply(response)

async def get_failed_list(message: Message):
    records = await get_list_by_status("🔴 Слетел")
    response = format_list(records, "Слетели")
    await message.reply(response)

async def help_handler(message: Message):
    help_text = (
        "/a {номер} — Добавить номер в ожидание.\n"
        "/c {номер} — Взять номер в холд.\n"
        "/success {номер} — Пометить номер как успешный.\n"
        "/s {номер} — Пометить номер как слетевший.\n"
        "/clear — Очистить все списки.\n"
        "/wl — Показать список ожидания.\n"
        "/hl — Показать список холда.\n"
        "/gl — Показать успешные номера.\n"
        "/sl — Показать слетевшие номера."
    )
    await message.reply(help_text)
