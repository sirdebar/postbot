import asyncpg
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta

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
    """
    Инициализирует базу данных, создает таблицы и добавляет первого админа.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Создаем таблицы, если они еще не существуют
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
                    hold_duration INTERVAL,
                    hold_time INTERVAL,
                    hold_set_by BIGINT REFERENCES users(user_id),
                    chat_id BIGINT
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON numbers (status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON numbers (timestamp)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_number ON numbers (number)")
        
        # Добавляем первого админа
        await add_first_admin()
        
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# database.py
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

async def add_first_admin():
    """
    Добавляет первого админа в таблицу users, если его еще нет.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Проверяем, есть ли уже админ в таблице
            admin_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM users WHERE is_admin = TRUE
                )
            """)
            
            if not admin_exists:
                # Добавляем первого админа
                first_admin_id = 7699005037
                await conn.execute("""
                    INSERT INTO users (user_id, is_admin)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE SET is_admin = $2
                """, first_admin_id, True)
                logger.info(f"First admin with user_id={first_admin_id} added.")
            else:
                logger.info("Admin already exists in the database.")
    except Exception as e:
        logger.error(f"Error adding first admin: {e}")
        raise

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

async def get_all_records(limit=10, last_id=None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if last_id:
            records = await conn.fetch("""
                SELECT id, number, user_id, status, timestamp, hold_start, hold_end, hold_duration 
                FROM numbers 
                WHERE id > $1 
                ORDER BY id 
                LIMIT $2
            """, last_id, limit)
        else:
            records = await conn.fetch("""
                SELECT id, number, user_id, status, timestamp, hold_start, hold_end, hold_duration 
                FROM numbers 
                ORDER BY id 
                LIMIT $2
            """, limit)
    return [dict(record) for record in records]

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

async def add_to_waiting(user_id, number, chat_id):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            existing = await conn.fetchval(""" 
                SELECT EXISTS(SELECT 1 FROM numbers WHERE number = $1) 
            """, number)
            if existing:
                return f"Номер {number} уже существует."
            await conn.execute(""" 
                INSERT INTO numbers (number, user_id, status, timestamp, chat_id) 
                VALUES ($1, $2, $3, $4, $5) 
            """, number, user_id, "🔵 Ожидание", datetime.now(timezone.utc), chat_id)
        return f"Номер {number} добавлен в список ожидания."
    except Exception as e:
        logger.error(f"Error adding to waiting list: {e}")
        return f"Произошла ошибка: {e}"

async def get_list_by_status(status, limit=10, offset=0):
    pool = await get_pool()
    async with pool.acquire() as conn:
        records = await conn.fetch("""
            SELECT id, number, user_id, status, timestamp, hold_start, hold_duration 
            FROM numbers 
            WHERE status = $1 
            ORDER BY timestamp ASC 
            LIMIT $2 OFFSET $3 
        """, status, limit, offset)
    records_dict = [dict(record) for record in records]
    for record in records_dict:
        if record.get('hold_start') and record.get('hold_duration'):
            elapsed = datetime.now(timezone.utc) - record['hold_start']
            record['elapsed_time'] = elapsed
        else:
            record['elapsed_time'] = None
    return records_dict

async def move_to_hold(number, hold_duration=None, hold_set_by=None, chat_id=None):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            hold_start = datetime.now(timezone.utc)
            if hold_duration:
                hold_end = hold_start + hold_duration
            else:
                hold_end = None
            await conn.execute(""" 
                UPDATE numbers 
                SET status = $2, hold_start = $3, hold_end = $4, hold_duration = $5, hold_set_by = $6, chat_id = $7 
                WHERE number = $1 AND status = $8 
            """, number, "🟠 Холдинг", hold_start, hold_end, hold_duration, hold_set_by, chat_id, "🔵 Ожидание")
        return f"Номер {number} взят в холд."
    except Exception as e:
        logger.error(f"Error moving to hold: {e}")
        return f"Произошла ошибка: {e}"

async def mark_as_successful(number, chat_id, bot):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Fetch user_id and hold_set_by before updating
            record = await conn.fetchrow("""
                SELECT user_id, hold_set_by, hold_start
                FROM numbers
                WHERE number = $1 AND status = $2
            """, number, "🟠 Холдинг")
            if not record:
                return "Номер не найден в холде."
            
            user_id = record['user_id']
            hold_set_by = record['hold_set_by']
            hold_start = record['hold_start']
            
            if hold_start:
                elapsed_time = datetime.now(timezone.utc) - hold_start
                await conn.execute(""" 
                    UPDATE numbers 
                    SET status = $2, hold_end = $3, hold_time = $4 
                    WHERE number = $1 AND status = $5 
                """, number, "🟢 Успешно", datetime.now(timezone.utc), elapsed_time, "🟠 Холдинг")
            else:
                await conn.execute(""" 
                    UPDATE numbers 
                    SET status = $2, hold_end = $3 
                    WHERE number = $1 AND status = $4 
                """, number, "🟢 Успешно", datetime.now(timezone.utc), "🟠 Холдинг")
        
        # Fetch user information
        try:
            worker_user = await bot.get_chat(user_id)
            worker_tag = f"<a href='tg://user?id={worker_user.id}'>{worker_user.full_name}</a>"
        except:
            worker_tag = "Пользователь не найден"
        
        if hold_set_by:
            try:
                admin_user = await bot.get_chat(hold_set_by)
                admin_tag = f"<a href='tg://user?id={admin_user.id}'>{admin_user.full_name}</a>"
            except:
                admin_tag = "Пользователь не найден"
        else:
            admin_tag = "Не указан"
        
        # Prepare the message
        elapsed_str = f"{elapsed_time.days}d {elapsed_time.seconds // 3600}h {(elapsed_time.seconds % 3600) // 60}m"
        message_text = (
            f"Номер {number} успешно отстоял холд!\n"
            f"Залил: {worker_tag}\n"
            f"Поставил: {admin_tag}\n"
            f"Отстоял: {elapsed_str}"
        )
        
        # Send the message to the specified chat
        await bot.send_message(chat_id=chat_id, text=message_text, parse_mode="HTML")
        
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
                elapsed_time = datetime.now(timezone.utc) - hold_start
                await conn.execute("""
                    UPDATE numbers 
                    SET status = $2, hold_time = $3 
                    WHERE number = $1 AND status = $4
                """, number, "🔴 Слетел", elapsed_time, "🟠 Холдинг")
            else:
                await conn.execute("""
                    UPDATE numbers 
                    SET status = $2 
                    WHERE number = $1 AND status = $3
                """, number, "🔴 Слетел", "🟠 Холдинг")
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