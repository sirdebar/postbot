import asyncpg
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_pool = None

async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(""" 
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        await conn.execute(""" 
            CREATE TABLE IF NOT EXISTS numbers (
                id SERIAL PRIMARY KEY,
                number TEXT NOT NULL,
                user_id BIGINT NOT NULL,
                status TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                hold_start TIMESTAMPTZ,
                hold_end TIMESTAMPTZ,
                hold_duration INTERVAL
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON numbers (status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON numbers (timestamp)")
    logger.info("Table setup complete.")

async def get_pool():
    global _pool
    if _pool is None:
        try:
            logger.info(f"Creating PostgreSQL connection pool with host={DB_HOST}, port={DB_PORT}, user={DB_USER}, database={DB_NAME}")
            _pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            logger.info("PostgreSQL connection pool created.")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise RuntimeError("Failed to create database connection pool") from e
    return _pool

async def delete_expired_records():
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            expiration_time = datetime.now(timezone.utc) - timedelta(days=1)
            await conn.execute(""" 
                DELETE FROM numbers WHERE timestamp < $1
            """, expiration_time)
            logger.info("Expired records deleted.")
    except Exception as e:
        logger.error(f"Error deleting records: {e}")

async def get_all_records(limit=10, offset=0):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            records = await conn.fetch(""" 
                SELECT id, number, user_id, status, timestamp, hold_start, hold_end, hold_duration 
                FROM numbers 
                ORDER BY timestamp ASC 
                LIMIT $1 OFFSET $2 
            """, limit, offset)
        return [dict(record) for record in records]
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
        return []

async def count_records(user_id=None, status=None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = "SELECT COUNT(*) FROM numbers"
        args = []
        if user_id and status:
            query += " WHERE user_id = $1 AND status = $2"
            args = [user_id, status]
        elif user_id:
            query += " WHERE user_id = $1"
            args = [user_id]
        elif status:
            query += " WHERE status = $1"
            args = [status]
        count = await conn.fetchval(query, *args)
    return count if count else 0

async def find_record_by_number(number):
    pool = await get_pool()
    async with pool.acquire() as conn:
        record = await conn.fetchrow(""" 
            SELECT id, number, user_id, status, timestamp, hold_start, hold_end, hold_duration 
            FROM numbers 
            WHERE number = $1 
        """, number)
    return dict(record) if record else None

async def add_to_waiting(user_id, number):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            existing = await conn.fetchval(""" 
                SELECT EXISTS(SELECT 1 FROM numbers WHERE number = $1) 
            """, number)
            if existing:
                return f"Номер {number} уже существует."
            await conn.execute(""" 
                INSERT INTO numbers (number, user_id, status, timestamp) 
                VALUES ($1, $2, $3, $4) 
            """, number, user_id, "🔵 Ожидание", datetime.now(timezone.utc))
        return f"Номер {number} добавлен в список ожидания."
    except Exception as e:
        logger.error(f"Error adding to waiting list: {e}")
        return f"Произошла ошибка: {e}"

async def get_list_by_status(status, limit=10, offset=0):
    pool = await get_pool()
    async with pool.acquire() as conn:
        records = await conn.fetch(""" 
            SELECT id, number, user_id, status, timestamp, hold_start, hold_end, hold_duration 
            FROM numbers 
            WHERE status = $1 
            ORDER BY timestamp ASC 
            LIMIT $2 OFFSET $3 
        """, status, limit, offset)
    return [dict(record) for record in records]

async def move_to_hold(number, hold_duration=None):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(""" 
                UPDATE numbers 
                SET status = $2, hold_start = $3, hold_end = $4, hold_duration = $5 
                WHERE number = $1 AND status = $6 
            """, number, "🟠 Холдинг", datetime.now(timezone.utc), datetime.now(timezone.utc) + hold_duration if hold_duration else None, hold_duration, "🔵 Ожидание")
        return f"Номер {number} взят в холд."
    except Exception as e:
        logger.error(f"Error moving to hold: {e}")
        return f"Произошла ошибка: {e}"

async def mark_as_successful(number):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            hold_start = await conn.fetchval("SELECT hold_start FROM numbers WHERE number = $1", number)
            if hold_start:
                hold_duration = datetime.now(timezone.utc) - hold_start
            else:
                hold_duration = None
            await conn.execute(""" 
                UPDATE numbers 
                SET status = $2, hold_end = $3, hold_duration = $4 
                WHERE number = $1 AND status = $5 
            """, number, "🟢 Успешно", datetime.now(timezone.utc), hold_duration, "🟠 Холдинг")
        return f"Номер {number} успешно завершил холд."
    except Exception as e:
        logger.error(f"Error marking as successful: {e}")
        return f"Произошла ошибка: {e}"

async def mark_as_failed(number):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            hold_start = await conn.fetchval("SELECT hold_start FROM numbers WHERE number = $1", number)
            if hold_start:
                hold_duration = datetime.now(timezone.utc) - hold_start
            else:
                hold_duration = None
            await conn.execute(""" 
                UPDATE numbers 
                SET status = $2, hold_end = $3, hold_duration = $4 
                WHERE number = $1 AND status = $5 
            """, number, "🔴 Слетел", datetime.now(timezone.utc), hold_duration, "🟠 Холдинг")
        return f"Номер {number} помечен как слетевший."
    except Exception as e:
        logger.error(f"Error marking as failed: {e}")
        return f"Произошла ошибка: {e}"

async def clear_all():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM numbers")
        return "Все списки очищены."
    except Exception as e:
        logger.error(f"Error clearing all records: {e}")
        return f"Произошла ошибка: {e}"

async def set_user_admin(user_id, is_admin=True):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(""" 
            INSERT INTO users (user_id, is_admin) 
            VALUES ($1, $2) 
            ON CONFLICT (user_id) DO UPDATE SET is_admin = $2 
        """, user_id, is_admin)

async def is_admin(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        is_admin = await conn.fetchval(""" 
            SELECT is_admin FROM users WHERE user_id = $1 
        """, user_id)
    return is_admin if is_admin is not None else False

async def get_user_numbers(user_id, status=None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if status:
            records = await conn.fetch(""" 
                SELECT id, number, status, timestamp, hold_start, hold_end, hold_duration 
                FROM numbers 
                WHERE user_id = $1 AND status = $2 
            """, user_id, status)
        else:
            records = await conn.fetch(""" 
                SELECT id, number, status, timestamp, hold_start, hold_end, hold_duration 
                FROM numbers 
                WHERE user_id = $1 
            """, user_id)
    return [dict(record) for record in records]

async def delete_number(number):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(""" 
                DELETE FROM numbers WHERE number = $1 
            """, number)
        return f"Номер {number} удален из списка ожидания."
    except Exception as e:
        logger.error(f"Error deleting number: {e}")
        return f"Произошла ошибка: {e}"