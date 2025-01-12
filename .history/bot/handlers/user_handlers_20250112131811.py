# handlers/user_handlers.py
from aiogram import Dispatcher
from aiogram.types import Message, CommandObject
from aiogram.filters import Command
from bot.database import (
    add_to_waiting, get_user_numbers, count_records, get_list_by_status, is_admin
)
from bot.utils import build_pagination_keyboard, format_list

async def add_number_handler(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /a 123456789")
        return

    number = args[1]
    response = await add_to_waiting(message.from_user.id, number)
    await message.reply(response)

async def my_handler(message: Message, command: CommandObject):
    target_user = message.from_user
    if command.args:
        if not await is_admin(message.from_user.id):
            await message.reply("У вас нет доступа к этой команде.")
            return
        try:
            user_id = int(command.args)
        except ValueError:
            await message.reply("Неверный формат user_id.")
            return
        target_user = await message.bot.get_chat(user_id)
    counts = await format_user_numbers_counts(target_user.id)
    response = (
        f"Статистика для {target_user.full_name} (id: {target_user.id}):\n\n"
        f"{counts}"
    )
    await message.reply(response, parse_mode="Markdown")

async def format_user_numbers_counts(user_id):
    waiting = await count_records(user_id=user_id, status="🔵 Ожидание")
    holding = await count_records(user_id=user_id, status="🟠 Холдинг")
    successful = await count_records(user_id=user_id, status="🟢 Успешно")
    failed = await count_records(user_id=user_id, status="🔴 Слетел")
    return (
        f"Ожидание: {waiting}\n"
        f"Холд: {holding}\n"
        f"Успешные: {successful}\n"
        f"Слетевшие: {failed}"
    )

async def get_waiting_list(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    limit = 10
    offset = 0
    current_page = 1
    total_records = await count_records(status="🔵 Ожидание")
    total_pages = (total_records + limit - 1) // limit
    records = await get_list_by_status("🔵 Ожидание", limit=limit, offset=offset)
    records = await add_user_tags(records, message.bot)
    response = format_list(records, "Ожидание", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages, status="🔵 Ожидание")
    await message.reply(response, reply_markup=keyboard, parse_mode="HTML")

async def get_hold_list(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    limit = 10
    offset = 0
    current_page = 1
    total_records = await count_records(status="🟠 Холдинг")
    total_pages = (total_records + limit - 1) // limit
    records = await get_list_by_status("🟠 Холдинг", limit=limit, offset=offset)
    records = await add_user_tags(records, message.bot)
    response = format_list(records, "Холдинг", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages, status="🟠 Холдинг")
    await message.reply(response, reply_markup=keyboard, parse_mode="HTML")

async def get_successful_list(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    limit = 10
    offset = 0
    current_page = 1
    total_records = await count_records(status="🟢 Успешно")
    total_pages = (total_records + limit - 1) // limit
    records = await get_list_by_status("🟢 Успешно", limit=limit, offset=offset)
    records = await add_user_tags(records, message.bot)
    response = format_list(records, "Успешно", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages, status="🟢 Успешно")
    await message.reply(response, reply_markup=keyboard, parse_mode="HTML")

async def get_failed_list(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    limit = 10
    offset = 0
    current_page = 1
    total_records = await count_records(status="🔴 Слетел")
    total_pages = (total_records + limit - 1) // limit
    records = await get_list_by_status("🔴 Слетел", limit=limit, offset=offset)
    records = await add_user_tags(records, message.bot)
    response = format_list(records, "Слетели", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages, status="🔴 Слетел")
    await message.reply(response, reply_markup=keyboard, parse_mode="HTML")

async def add_user_tags(records, bot):
    for record in records:
        try:
            user = await bot.get_chat(record['user_id'])
            record['user_tag'] = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
        except:
            record['user_tag'] = "Пользователь не найден"
    return records

def register_user_handlers(dp: Dispatcher):
    dp.message.register(add_number_handler, Command(commands=["a"]))
    dp.message.register(my_handler, Command(commands=["my"]))
    dp.message.register(get_waiting_list, Command(commands=["wl"]))
    dp.message.register(get_hold_list, Command(commands=["hl"]))
    dp.message.register(get_successful_list, Command(commands=["gl"]))
    dp.message.register(get_failed_list, Command(commands=["sl"]))