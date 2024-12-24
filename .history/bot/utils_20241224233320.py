from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_pagination_keyboard(current_page, total_pages):
    keyboard = InlineKeyboardBuilder()
    if current_page > 1:
        keyboard.button(text="<", callback_data=f"page:{current_page - 1}")
    if current_page < total_pages:
        keyboard.button(text=">", callback_data=f"page:{current_page + 1}")
    return keyboard.as_markup()

def format_list(records, title):
    """
    Форматирует список записей для отображения в сообщении.
    """
    if not records:
        return f"Список {title} пуст."

    result = [
        f"{idx + 1}: {record[2]} {record[1]} {record[3]}"
        for idx, record in enumerate(records)
    ]
    return "\n".join(result)

