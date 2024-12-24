def format_list(records, title):
    if not records:
        return f"Список {title} пуст."

    result = [f"{idx + 1}: {record[2]} {record[1]} {record[3]}" for idx, record in enumerate(records)]
    return "\n".join(result)
