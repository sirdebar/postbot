from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_pagination_keyboard(current_page, total_pages, status=None):
    keyboard = InlineKeyboardBuilder()
    callback_base = f"page:{status}:" if status else "page:all:"

    if current_page > 1:
        keyboard.button(text="<", callback_data=f"{callback_base}{current_page - 1}")
    if current_page < total_pages:
        keyboard.button(text=">", callback_data=f"{callback_base}{current_page + 1}")
    if status:
        keyboard.button(text="Найти", callback_data=f"search:{status}")
    else:
        keyboard.button(text="Найти", callback_data="search:all")

    return keyboard.as_markup()

def format_hold_duration(hold_duration):
    if hold_duration is None:
        return ""
    hours = hold_duration.seconds // 3600
    minutes = (hold_duration.seconds // 60) % 60
    return f"{hours}h {minutes}m"

def format_list(records, title, current_page, total_pages):
    if not records:
        return f"Список {title} пуст."

    header = f"**{title} (стр. {current_page}/{total_pages}):**\n"
    body = "\n".join([
        f"{i+1}. {record['user_tag']} {record['number']} {record['status']} [{format_hold_duration(record['hold_duration']) if record['hold_duration'] else ''}]"
        for i, record in enumerate(records)
    ])
    return header + body

# bot/utils.py
from redis.asyncio import Redis

redis = None

def set_redis(r):
    global redis
    redis = r

def get_redis():
    return redis