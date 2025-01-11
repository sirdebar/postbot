from aiogram import Dispatcher, Bot
from aiogram.types import Message, CallbackQuery, User, ChatMemberUpdated
from aiogram.filters import Command, CommandObject, ChatMemberUpdatedFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils import build_pagination_keyboard, format_list
from bot.database import (
    add_to_waiting, move_to_hold, mark_as_successful, mark_as_failed, clear_all,
    get_list_by_status, get_all_records, count_records, find_record_by_number,
    set_user_admin, is_admin, get_user_numbers, delete_number
)

class SearchStates(StatesGroup):
    waiting_for_number = State()

class IsNewChatMemberFilter(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated) -> bool:
        return event.old_chat_member.status == "left" and event.new_chat_member.status == "member"

def setup_handlers(dp: Dispatcher, redis):

def setup_handlers(dp: Dispatcher):
    dp.message.register(search_handler, Command(commands=["search"]))
    dp.message.register(number_search_handler, SearchStates.waiting_for_number)
    dp.message.register(add_number_handler, Command(commands=["a"]))
    dp.message.register(hold_number_handler, Command(commands=["c"]))
    dp.message.register(successful_number_handler, Command(commands=["success"]))
    dp.message.register(failed_number_handler, Command(commands=["s"]))
    dp.message.register(clear_all_handler, Command(commands=["clear"]))
    dp.message.register(get_waiting_list, Command(commands=["wl"]))
    dp.message.register(get_hold_list, Command(commands=["hl"]))
    dp.message.register(get_successful_list, Command(commands=["gl"]))
    dp.message.register(get_failed_list, Command(commands=["sl"]))
    dp.message.register(list_all_handler, Command(commands=["l"]))
    dp.message.register(help_handler, Command(commands=["help"]))
    dp.message.register(admin_handler, Command(commands=["admin"]))
    dp.message.register(deladmin_handler, Command(commands=["deladmin"]))
    dp.message.register(my_handler, Command(commands=["my"]))
    dp.message.register(stata_handler, Command(commands=["stata"]))
    dp.message.register(set_hold_duration_handler, Command(commands=["h"]))
    dp.message.register(delete_number_handler, Command(commands=["aa"]))
    dp.callback_query.register(paginate_list, lambda c: c.data.startswith("page:"))
    dp.callback_query.register(search_handler, lambda c: c.data.startswith("search:"))
    dp.chat_member.register(user_joined_handler, IsNewChatMemberFilter())

async def user_joined_handler(event: ChatMemberUpdated):
    user_id = event.new_chat_member.user.id
    await set_user_admin(user_id, is_admin=False)

async def paginate_list(callback: CallbackQuery):
    _, status, current_page = callback.data.split(":")
    current_page = int(current_page)
    limit = 10
    offset = (current_page - 1) * limit

    if status == "all":
        records = await get_all_records(limit=limit, offset=offset)
        total_records = await count_records()
        title = "Общий список"
    else:
        records = await get_list_by_status(status, limit=limit, offset=offset)
        total_records = await count_records(status=status)
        title = f"Список по статусу {status}"

    total_pages = (total_records + limit - 1) // limit

    if not records:
        response = f"{title} пуст."
    else:
        response = format_list(records, title, current_page, total_pages)

    keyboard = build_pagination_keyboard(current_page, total_pages, status)
    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")

async def search_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.reply("Введите номер для поиска:")
    await state.set_state(SearchStates.waiting_for_number)


async def number_search_handler(message: Message, state: FSMContext):
    number = message.text.strip()
    record = await find_record_by_number(number)
    if record:
        try:
            user = await message.bot.get_chat(record['user_id'])
            user_tag = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
        except:
            user_tag = "Пользователь не найден"
        response = (
            f"Найден номер:\n"
            f"ID: {record['id']}\n"
            f"Номер: {record['number']}\n"
            f"Пользователь: {user_tag}\n"
            f"Статус: {record['status']}\n"
            f"Дата: {record['timestamp'].strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        response = f"Номер {number} не найден."
    await message.reply(response, parse_mode="HTML")
    await state.clear()

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

async def list_all_handler(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    limit = 10
    offset = 0
    current_page = 1
    records = await get_all_records(limit=limit, offset=offset)
    total_records = await count_records()
    total_pages = (total_records + limit - 1) // limit

    if not records:
        response = "Список пуст."
    else:
        response = format_list(records, "Общий список всех номеров", current_page, total_pages)

    keyboard = build_pagination_keyboard(current_page, total_pages, status="all")
    await message.reply(response, reply_markup=keyboard, parse_mode="Markdown")

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

async def clear_all_handler(message: Message):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    response = await clear_all()
    await message.reply(response)

async def add_user_tags(records, bot):
    for record in records:
        try:
            user = await bot.get_chat(record['user_id'])
            record['user_tag'] = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
        except:
            record['user_tag'] = "Пользователь не найден"
    return records

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

async def admin_handler(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к этой команде.")
        return
    if not command.args:
        await message.reply("Укажите user_id или username пользователя! Пример: /admin 123456789 или /admin @username")
        return
    user_input = command.args
    if user_input.startswith("@"):
        # Fetch user by username
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
        # Fetch user by username
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