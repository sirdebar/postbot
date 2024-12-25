from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.middleware import FSMContextMiddleware
from aiogram.fsm.state import State, StatesGroup
from bot.utils import build_pagination_keyboard, format_list
from bot.database import (
    add_to_waiting, move_to_hold, mark_as_successful, mark_as_failed, clear_all,
    get_list_by_status, get_all_records, count_records, find_record_by_number
)

class SearchStates(StatesGroup):
    waiting_for_number = State()

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

def setup_handlers(dp: Dispatcher):
    dp.message.middleware(FSMContextMiddleware(storage=dp.storage))
    dp.callback_query.register(search_handler, lambda c: c.data.startswith("search:"))
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

    # Обработчики для пагинации и поиска
    dp.callback_query.register(paginate_list, lambda c: c.data.startswith("page:"))
    dp.callback_query.register(search_handler, lambda c: c.data.startswith("search:"))

async def paginate_list(callback: CallbackQuery):
    """
    Обрабатывает нажатия на кнопки пагинации.
    """
    _, status, current_page = callback.data.split(":")
    current_page = int(current_page)
    limit = 10
    offset = (current_page - 1) * limit

    # Получение записей и установка title
    if status == "all":
        records = await get_all_records(limit=limit, offset=offset)
        total_records = await count_records()
        title = "Общий список"
    else:
        records = await get_list_by_status(status, limit=limit, offset=offset)
        total_records = await count_records(status)
        title = "Список по статусу"  # Добавлено для отсутствующего заголовка

    total_pages = (total_records + limit - 1) // limit  # Подсчёт количества страниц

    # Проверка на корректность данных
    if not records:
        title = title or "Список"
        response = f"{title} пуст."  # Обработка пустого списка
    else:
        response = format_list(records, title, current_page, total_pages)  # Форматирование списка
    
    keyboard = build_pagination_keyboard(current_page, total_pages, status)

    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")

async def number_search_handler(message: Message, state: FSMContext):
    number = message.text.strip()
    record = await find_record_by_number(number)
    if record:
        response = f"Найден номер:\n" \
                   f"ID: {record[0]}\n" \
                   f"Номер: {record[1]}\n" \
                   f"Пользователь: @{record[2]}\n" \
                   f"Статус: {record[3]}\n" \
                   f"Дата: {record[4]}"
    else:
        response = f"Номер {number} не найден."
    await message.reply(response)
    await state.clear()

async def search_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.reply("Введите номер для поиска:")
    await state.set_state(SearchStates.waiting_for_number)

async def add_number_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номер! Пример: /a 123456789")
        return

    number = args[1]
    user_tag = message.from_user.username or "Без тега"
    response = await add_to_waiting(user_tag, number)
    await message.reply(response)

async def list_all_handler(message: Message):
    """
    Выводит первую страницу общего списка.
    """
    limit = 10
    offset = 0
    current_page = 1

    total_records = await count_records()
    total_pages = (total_records + limit - 1) // limit
    records = await get_all_records(limit=limit, offset=offset)

    # Исправленный вызов format_list
    response = format_list(records, "Общий список всех номеров", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages)

    await message.reply(response, reply_markup=keyboard, parse_mode="Markdown")



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

async def get_waiting_list(message: Message):
    limit = 10
    offset = 0
    current_page = 1

    total_records = await count_records("🔵 Ожидание")
    total_pages = (total_records + limit - 1) // limit
    records = await get_list_by_status("🔵 Ожидание", limit=limit, offset=offset)

    # Исправленный вызов format_list
    response = format_list(records, "Ожидание", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages, status="🔵 Ожидание")

    await message.reply(response, reply_markup=keyboard, parse_mode="Markdown")


async def get_hold_list(message: Message):
    limit = 10
    offset = 0
    current_page = 1

    total_records = await count_records("🟠 Холдинг")
    total_pages = (total_records + limit - 1) // limit
    records = await get_list_by_status("🟠 Холдинг", limit=limit, offset=offset)

    # Исправленный вызов format_list
    response = format_list(records, "Холдинг", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages, status="🟠 Холдинг")

    await message.reply(response, reply_markup=keyboard, parse_mode="Markdown")


async def get_successful_list(message: Message):
    limit = 10
    offset = 0
    current_page = 1

    total_records = await count_records("🟢 Успешно")
    total_pages = (total_records + limit - 1) // limit
    records = await get_list_by_status("🟢 Успешно", limit=limit, offset=offset)

    # Исправленный вызов format_list
    response = format_list(records, "Успешно", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages, status="🟢 Успешно")

    await message.reply(response, reply_markup=keyboard, parse_mode="Markdown")


async def get_failed_list(message: Message):
    limit = 10
    offset = 0
    current_page = 1

    total_records = await count_records("🔴 Слетел")
    total_pages = (total_records + limit - 1) // limit
    records = await get_list_by_status("🔴 Слетел", limit=limit, offset=offset)

    # Исправленный вызов format_list
    response = format_list(records, "Слетели", current_page, total_pages)
    keyboard = build_pagination_keyboard(current_page, total_pages, status="🔴 Слетел")

    await message.reply(response, reply_markup=keyboard, parse_mode="Markdown")


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
