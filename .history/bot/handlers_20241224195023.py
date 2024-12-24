from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from bot.storage import (
    add_to_waiting, move_to_hold, mark_as_successful, mark_as_failed, clear_all
)

def setup_handlers(dp: Dispatcher):
    dp.message.register(add_number_handler, Command("a"))
    dp.message.register(hold_number_handler, Command("c"))
    dp.message.register(successful_number_handler, Command("success"))
    dp.message.register(failed_number_handler, Command("s"))
    dp.message.register(clear_all_handler, Command("clear"))

async def add_number_handler(message: Message, command: Command.Object):
    if not command.args:
        await message.reply("Укажите номер! Пример: /a 123456789")
        return

    number = command.args
    user = message.from_user.mention
    response = await add_to_waiting(user, number)
    await message.reply(response)

async def hold_number_handler(message: Message, command: Command.Object):
    if not command.args:
        await message.reply("Укажите номер! Пример: /c 123456789")
        return

    number = command.args
    response = await move_to_hold(number)
    await message.reply(response)

async def successful_number_handler(message: Message, command: Command.Object):
    if not command.args:
        await message.reply("Укажите номер! Пример: /success 123456789")
        return

    number = command.args
    response = await mark_as_successful(number)
    await message.reply(response)

async def failed_number_handler(message: Message, command: Command.Object):
    if not command.args:
        await message.reply("Укажите номер! Пример: /s 123456789")
        return

    number = command.args
    response = await mark_as_failed(number)
    await message.reply(response)

async def clear_all_handler(message: Message):
    await clear_all()
    await message.reply("Все списки очищены.")
