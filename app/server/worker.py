import asyncio
import logging

from apps.neda.worker import check_open_voice_convert_status
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from server.config import Settings

# import pytz
# irst_timezone = pytz.timezone("Asia/Tehran")
logging.getLogger("apscheduler").setLevel(logging.WARNING)


async def worker():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_open_voice_convert_status, "interval", seconds=Settings.worker_update_time
    )

    scheduler.start()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
