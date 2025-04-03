import asyncio

from fastapi_mongo_base.tasks import TaskStatusEnum

from .models import VoiceConvert
from .services import check_open_voice_convert_status


async def update_voice_convert():
    data: list[VoiceConvert] = (
        await VoiceConvert.get_query()
        .find(
            {
                "task_status": {"$in": [TaskStatusEnum.processing]},
            }
        )
        .to_list()
    )
    for voice_convert in data:
        asyncio.create_task(check_open_voice_convert_status(voice_convert))
