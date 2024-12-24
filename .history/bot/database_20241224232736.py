import aiosqlite
from datetime import datetime, timedelta

DB_PATH = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL,
            user TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            hold_start DATETIME,
            hold_end DATETIME
        )
        """)
        await db.commit()

async def add_to_waiting(user, number):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO numbers (number, user, status, timestamp)
        VALUES (?, ?, ?, ?)
        """, (number, user, "🔵 Ожидание", datetime.now()))
        await db.commit()
        return f"Номер {number} добавлен в список ожидания."

async def get_list_by_status(status, limit=20, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT id, number, user, status, timestamp FROM numbers
        WHERE status = ?
        ORDER BY timestamp ASC
        LIMIT ? OFFSET ?
        """, (status, limit, offset)) as cursor:
            return await cursor.fetchall()

async def move_to_hold(number):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE numbers
        SET status = ?, hold_start = ?, hold_end = ?
        WHERE number = ? AND status = ?
        """, ("🟠 Холдинг", datetime.now(), datetime.now() + timedelta(hours=3), number, "🔵 Ожидание"))
        changes = db.total_changes
        await db.commit()
        if changes > 0:
            return f"Номер {number} взят в холд."
        return f"Номер {number} не найден в списке ожидания."

async def mark_as_successful(number):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE numbers
        SET status = ?, hold_end = ?
        WHERE number = ? AND status = ?
        """, ("🟢 Успешно", datetime.now(), number, "🟠 Холдинг"))
        changes = db.total_changes
        await db.commit()
        if changes > 0:
            return f"Номер {number} успешно завершил холд."
        return f"Номер {number} не найден в списке холда."

async def mark_as_failed(number):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE numbers
        SET status = ?, hold_end = ?
        WHERE number = ? AND status = ?
        """, ("🔴 Слетел", datetime.now(), number, "🟠 Холдинг"))
        changes = db.total_changes
        await db.commit()
        if changes > 0:
            return f"Номер {number} помечен как слетевший."
        return f"Номер {number} не найден в списке холда."

async def clear_all():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM numbers")
        await db.commit()
        return "Все списки очищены."
