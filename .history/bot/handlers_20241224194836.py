from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Text
from bot.storage import add_to_waiting, get_paginated_list, find_number, update_status, clear_all
from bot.utils import build_pagination_keyboard
from bot.timers import start_timer

# Регистрация команд
def setup_handlers(dp: Dispatcher):
    dp.message.register(add_number_handler, Command("a"))
    dp.message.register(list_numbers_handler, Command("l"))
    dp.message.register(hold_number_handler, Command("c"))
    dp.message.register(mark_failed_handler, Command("s"))
    dp.message.register(clear_all_handler, Command("clear"))
    dp.callback_query.register(handle_pagination, Text(startswith="page:"))

async def add_number_handler(message: Message, command: Command.Object):
    if not command.args:
        await message.reply("Укажите номер! Пример: /a 123456789")
        return

    number = command.args
    user_tag = message.from_user.mention
    result = add_to_waiting(user_tag, number)
    await message.reply(result)

async def list_numbers_handler(message: Message, command: Command.Object):
    page = 1
    response, keyboard = get_paginated_list(page)
    await message.reply(response, reply_markup=keyboard)

async def hold_number_handler(message: Message, command: Command.Object):
    if not command.args:
        await message.reply("Укажите номер! Пример: /c 123456789")
        return

    number = command.args
    result, timer = update_status(number, "hold")
    if result:
        await message.reply(f"Номер {number} взят в холд на 3 часа.")
        start_timer(number, timer)  # Запуск таймера
    else:
        await message.reply("Номер не найден в списке ожидания.")

async def mark_failed_handler(message: Message, command: Command.Object):
    if not command.args:
        await message.reply("Укажите номер! Пример: /s 123456789")
        return

    number = command.args
    result = update_status(number, "failed")
    await message.reply(result)

async def clear_all_handler(message: Message):
    clear_all()
    await message.reply("Все списки очищены.")

async def handle_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    response, keyboard = get_paginated_list(page)
    await callback.message.edit_text(response, reply_markup=keyboard)
