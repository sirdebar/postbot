from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_pagination_keyboard(current_page, total_pages):
    keyboard = InlineKeyboardBuilder()
    if current_page > 1:
        keyboard.button(text="<", callback_data=f"page:{current_page - 1}")
    if current_page < total_pages:
        keyboard.button(text=">", callback_data=f"page:{current_page + 1}")
    return keyboard.as_markup()
