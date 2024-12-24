from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from bot.database import (
    add_to_waiting, move_to_hold, mark_as_successful, mark_as_failed, clear_all
)

def setup_handlers(dp: Dispatcher):
    dp.message.register(add_number_handler, Command(commands=["a"]))
    dp.message.register(hold_number_handler, Command(commands=["c"]))
    dp.message.register(successful_number_handler, Command(commands=["success"]))
    dp.message.register(failed_number_handler, Command(commands=["s"]))
    dp.message.register(clear_all_handler, Command(commands=["clear"]))

async def add_number_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /a 123456789")
        return

    number = args[1]
    user_id = message.from_user.id
    user_name = message.from_user.full_name or "Без имени"
    user_mention = f"[{user_name}](tg://user?id={user_id})"
    response = await add_to_waiting(user_mention, number)
    await message.reply(response, parse_mode="Markdown")

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
