import logging
from io import BytesIO

import httpx
from aiocache import cached
from apps.voice.models import VoiceModel
from server.config import Settings
from utils import finance, voice, media

from .models import VoiceConvert
from .schemas import VoiceConvertStatus, PredictionModelWebhookData


@cached(ttl=60)
async def get_voice(url: str) -> BytesIO:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return BytesIO(response.content)


async def register_cost(voice_task: VoiceConvert):
    duration = voice.get_duration(await get_voice(voice_task.url))
    price = Settings.minutes_price * duration
    usage = await finance.meter_cost(voice_task.user_id, amount=price)
    if usage:
        return usage

    logging.error(f"Insufficient balance. {voice_task.user_id} {voice_task.id}")
    await voice_task.fail("Insufficient balance.")


async def convert_voice(voice_task: VoiceConvert, **kwargs):
    usage = await register_cost(voice_task)

    if usage is None:
        return

    model = await VoiceModel.get_by_slug(voice_task.target_voice)
    # pitch_data = voice.calculate_voice_pitch(await get_voice(voice_task.url))
    replicate_id = voice.create_rvc_conversion(
        voice_task.url,
        model.model_url,
        voice_task.pitch_difference,
        voice_task.item_webhook_url,
    )

    voice_task._status = VoiceConvertStatus.voice_change
    voice_task.replicate_id = replicate_id
    await voice_task.save()


async def process_convert_voice_webhook(voice_task: VoiceConvert, data: PredictionModelWebhookData):
    if voice_task.status == VoiceConvertStatus.voice_change:
        output_url = await media.upload_file(
            data.output,
            file_name=f"{voice_task.target_voice}.wav",
            user_id=voice_task.user_id,
        )
        voice_task._status = VoiceConvertStatus.completed
        voice_task.output_url = output_url
        await voice_task.save()


async def check_open_voice_convert_status(voice_task: VoiceConvert):
    pass
