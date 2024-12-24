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

async def update_status(number, new_status, hold_start=None, hold_end=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE numbers
        SET status = ?, hold_start = ?, hold_end = ?
        WHERE number = ?
        """, (new_status, hold_start, hold_end, number))
        await db.commit()

async def get_records_by_status(status, limit=20, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT id, user, number, status, timestamp, hold_start, hold_end
        FROM numbers
        WHERE status = ?
        ORDER BY timestamp ASC
        LIMIT ? OFFSET ?
        """, (status, limit, offset)) as cursor:
            return await cursor.fetchall()

async def get_all_records(limit=20, offset=0):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT id, user, number, status, timestamp, hold_start, hold_end
        FROM numbers
        ORDER BY timestamp ASC
        LIMIT ? OFFSET ?
        """, (limit, offset)) as cursor:
            return await cursor.fetchall()

async def clear_all():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM numbers")
        await db.commit()
        return "Все списки очищены."
