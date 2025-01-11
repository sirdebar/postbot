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

def format_list(records, title, current_page, total_pages):
    if not records:
        return f"Список {title} пуст."

    header = f"**{title} (стр. {current_page}/{total_pages}):**\n"
    body = "\n".join([
        f"{idx + 1}: {record['number']} {record['status']} [{record['hold_duration'] if record['hold_duration'] else ''}]"
        for idx, record in enumerate(records)
    ])
    return header + body