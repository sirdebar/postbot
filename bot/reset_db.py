# reset_db.py
import asyncpg
import logging
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reset_database():
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    await conn.execute("DROP TABLE IF EXISTS users CASCADE")
    await conn.execute("DROP TABLE IF EXISTS numbers CASCADE")
    await conn.close()
    logger.warning("Database tables dropped.")

async def init_db():
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    await conn.execute(""" 
        CREATE TABLE users (
            user_id BIGINT PRIMARY KEY,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    await conn.execute(""" 
        CREATE TABLE numbers (
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
    await conn.close()
    logger.info("Database tables recreated.")

async def main():
    await reset_database()
    await init_db()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())