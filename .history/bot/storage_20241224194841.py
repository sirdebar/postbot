from datetime import datetime, timedelta
from aiogram.utils.keyboard import InlineKeyboardBuilder

storage = {
    "waiting": [],
    "hold": [],
    "successful": [],
    "failed": []
}

def add_to_waiting(user, number):
    entry = {
        "number": number,
        "user": user,
        "added_at": datetime.now(),
        "status": "🔵 Ожидание"
    }
    storage["waiting"].append(entry)
    return f"Номер {number} добавлен в список ожидания."

def find_number(number):
    for status, entries in storage.items():
        for entry in entries:
            if entry["number"] == number:
                return status, entry
    return None, None

def update_status(number, new_status):
    status, entry = find_number(number)
    if not entry:
        return f"Номер {number} не найден.", None

    if new_status == "hold":
        entry["status"] = "🟠 Холдинг"
        entry["hold_start"] = datetime.now()
        entry["hold_end"] = datetime.now() + timedelta(hours=3)
        storage["waiting"].remove(entry)
        storage["hold"].append(entry)
        return True, entry["hold_end"]
    
    if new_status == "failed":
        entry["status"] = "🔴 Слетел"
        entry["failed_at"] = datetime.now()
        storage["hold"].remove(entry)
        storage["failed"].append(entry)
        return f"Номер {number} слетел.", None

    return f"Некорректный статус: {new_status}.", None

def clear_all():
    for key in storage:
        storage[key].clear()

def get_paginated_list(page, per_page=20):
    all_numbers = storage["waiting"] + storage["hold"] + storage["successful"] + storage["failed"]
    total_pages = (len(all_numbers) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page

    def format_entry(idx, entry):
        return f"{idx}: {entry['user']} {entry['number']} {entry['status']}"

    page_numbers = [format_entry(i + 1, entry) for i, entry in enumerate(all_numbers[start:end])]

    keyboard = build_pagination_keyboard(page, total_pages)
    return "\n".join(page_numbers), keyboard
