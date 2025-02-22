from aiogram.utils.keyboard import InlineKeyboardBuilder
import pytz

def convert_utc_to_msk(utc_time):
    """
    Преобразует время из UTC в московское время (MSK).
    """
    msk_timezone = pytz.timezone('Europe/Moscow')
    return utc_time.astimezone(msk_timezone)

# utils.py
def build_pagination_keyboard(current_page, total_pages, status=None):
    keyboard = InlineKeyboardBuilder()
    if status:
        callback_base = f"page:{status}:"
    else:
        callback_base = "page:all:"
    
    if total_pages == 0:
        return keyboard.as_markup()
    
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
    days = hold_duration.days
    hours = hold_duration.seconds // 3600
    minutes = (hold_duration.seconds // 60) % 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    else:
        return f"{hours}h {minutes}m"

def format_list(records, title, current_page, total_pages):
    if not records:
        return f"Список {title} пуст."
    
    header = f"<b>{title} (стр. {current_page}/{total_pages}):</b>\n"
    body = "\n".join([
        f"{i+1}. {record['user_tag']} {record['number']} - {record['status']} [{'{:.0f}d {:.0f}h {:.0f}m'.format(record['elapsed_time'].days, record['elapsed_time'].seconds // 3600, (record['elapsed_time'].seconds % 3600) // 60)}]" if record['elapsed_time'] else
        f"{i+1}. {record['user_tag']} {record['number']} - {record['status']} [0d 0h 0m]"
        for i, record in enumerate(records)
    ])
    return header + body
