from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_pagination_keyboard(current_page, total_pages, status=None):
    """
    Создаёт клавиатуру для пагинации.
    """
    keyboard = InlineKeyboardBuilder()
    callback_base = f"page:{status}:" if status else "page:all:"

    if current_page > 1:
        keyboard.button(text="<", callback_data=f"{callback_base}{current_page - 1}")
    if current_page < total_pages:
        keyboard.button(text=">", callback_data=f"{callback_base}{current_page + 1}")
    keyboard.button(text="Найти", callback_data=f"search:{status}")

    return keyboard.as_markup()

def format_list(records, title, current_page, total_pages):
    """
    Форматирует список записей для отображения в сообщении.
    """
    if not records:
        return f"Список {title} пуст."

    header = f"**{title} (стр. {current_page}/{total_pages}):**\n"
    body = "\n".join([
        f"{idx + 1}: @{record[2]} {record[1]} {record[3]}" if record[2] != "Без тега" else
        f"{idx + 1}: Без_тега {record[1]} {record[3]}"
        for idx, record in enumerate(records)
    ])
    return header + body
