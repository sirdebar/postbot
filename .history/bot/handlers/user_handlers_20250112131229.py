# handlers/user_handlers.py
from aiogram import Dispatcher
from aiogram.types import Message, CommandObject
from aiogram.filters import Command
from bot.database import add_to_waiting, get_user_numbers, count_records

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

def register_user_handlers(dp: Dispatcher):
    dp.message.register(add_number_handler, Command(commands=["a"]))
    dp.message.register(my_handler, Command(commands=["my"]))