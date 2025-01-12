# handlers/search_handlers.py
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from bot.database import find_record_by_number, get_all_records, get_list_by_status, count_records
from bot.utils import build_pagination_keyboard, format_list
from datetime import datetime, timezone
import pytz

class SearchStates(StatesGroup):
    waiting_for_number = State()

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

        # Преобразуем время из UTC в MSK
        utc_time = record['timestamp']
        msk_timezone = pytz.timezone('Europe/Moscow')
        msk_time = utc_time.astimezone(msk_timezone)

        response = (
            f"Найден номер:\n"
            f"ID: {record['id']}\n"
            f"Номер: {record['number']}\n"
            f"Пользователь: {user_tag}\n"
            f"Статус: {record['status']}\n"
            f"Дата: {msk_time.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        response = f"Номер {number} не найден."
    await message.reply(response, parse_mode="HTML")
    await state.clear()

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

def register_search_handlers(dp: Dispatcher):
    dp.message.register(search_handler, Command(commands=["search"]))
    dp.message.register(number_search_handler, SearchStates.waiting_for_number)
    dp.callback_query.register(paginate_list, lambda c: c.data.startswith("page:"))