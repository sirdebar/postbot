import asyncio
from datetime import datetime
from bot.storage import update_status

async def start_timer(number, end_time):
    wait_time = (end_time - datetime.now()).total_seconds()
    await asyncio.sleep(wait_time)
    update_status(number, "successful")
