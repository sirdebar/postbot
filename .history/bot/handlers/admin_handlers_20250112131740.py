# handlers/admin_handlers.py
from aiogram import Dispatcher
from aiogram.types import Message, CommandObject
from aiogram.filters import Command
from datetime import timedelta
from bot.database import (
    set_user_admin, clear_all, delete_number, move_to_hold,
    mark_as_successful, mark_as_failed, is_admin
)

async def admin_handler(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
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
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
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

async def hold_number_handler(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /c 123456789")
        return

    number = args[1]
    # Get global hold duration from Redis
    hold_duration_str = await redis.get("global_hold_duration")
    if hold_duration_str:
        hold_duration = int(hold_duration_str)
        hold_duration_timedelta = timedelta(hours=hold_duration)
    else:
        hold_duration_timedelta = None
    response = await move_to_hold(number, hold_duration=hold_duration_timedelta)
    await message.reply(response)

async def successful_number_handler(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /success 123456789")
        return

    number = args[1]
    response = await mark_as_successful(number)
    await message.reply(response)

async def failed_number_handler(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /s 123456789")
        return

    number = args[1]
    response = await mark_as_failed(number)
    await message.reply(response)

async def set_hold_duration_handler(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    if not command.args:
        await message.reply("Укажите время в часах! Пример: /h 3")
        return
    try:
        hours = int(command.args)
        if hours < 0:
            raise ValueError
    except ValueError:
        await message.reply("Время должно быть неотрицательным числом.")
        return
    if hours == 0:
        # Set indefinite hold
        await redis.delete("global_hold_duration")
        hold_duration = None
    else:
        hold_duration = hours
        await redis.set("global_hold_duration", hold_duration)
    await message.reply(f"Время холда установлено на {hours} часов.")

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(admin_handler, Command(commands=["admin"]))
    dp.message.register(deladmin_handler, Command(commands=["deladmin"]))
    dp.message.register(clear_all_handler, Command(commands=["clear"]))
    dp.message.register(delete_number_handler, Command(commands=["aa"]))
    dp.message.register(hold_number_handler, Command(commands=["c"]))
    dp.message.register(successful_number_handler, Command(commands=["success"]))
    dp.message.register(failed_number_handler, Command(commands=["s"]))
    dp.message.register(set_hold_duration_handler, Command(commands=["h"]))