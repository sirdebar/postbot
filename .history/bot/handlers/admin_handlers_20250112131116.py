# handlers/admin_handlers.py
from aiogram import Dispatcher
from aiogram.types import Message, CommandObject
from aiogram.filters import Command
from bot.database import set_user_admin, clear_all, delete_number

async def admin_handler(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("Укажите user_id или username пользователя! Пример: /admin 123456789 или /admin @username")
        return
    user_input = command.args
    if user_input.startswith("@"):
        try:
            user = await message.bot.get_chat(user_input)
            user_id = user.id
        except Exception as e:
            await message.reply(f"Пользователь {user_input} не найден.")
            return
    else:
        try:
            user_id = int(user_input)
        except ValueError:
            await message.reply("Неверный формат user_id или username.")
            return
    await set_user_admin(user_id, is_admin=True)
    await message.reply(f"Пользователь {user_input} назначен администратором.")

async def deladmin_handler(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("Укажите user_id или username пользователя! Пример: /deladmin 123456789 или /deladmin @username")
        return
    user_input = command.args
    if user_input.startswith("@"):
        try:
            user = await message.bot.get_chat(user_input)
            user_id = user.id
        except Exception as e:
            await message.reply(f"Пользователь {user_input} не найден.")
            return
    else:
        try:
            user_id = int(user_input)
        except ValueError:
            await message.reply("Неверный формат user_id или username.")
            return
    await set_user_admin(user_id, is_admin=False)
    await message.reply(f"Пользователь {user_input} лишен админских прав.")

async def clear_all_handler(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    response = await clear_all()
    await message.reply(response)

async def delete_number_handler(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    if not command.args:
        await message.reply("Укажите номер! Пример: /aa 123456789")
        return
    number = command.args
    response = await delete_number(number)
    await message.reply(response)

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(admin_handler, Command(commands=["admin"]))
    dp.message.register(deladmin_handler, Command(commands=["deladmin"]))
    dp.message.register(clear_all_handler, Command(commands=["clear"]))
    dp.message.register(delete_number_handler, Command(commands=["aa"]))