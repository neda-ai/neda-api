import logging
from io import BytesIO

import httpx
from aiocache import cached
from apps.voice.models import VoiceModel
from server.config import Settings
from utils import finance, media, voice

from .models import VoiceConvert
from .schemas import (
    PredictionModelWebhookData,
    RunpodWebhookData,
    VoiceConvertStatus,
)


@cached(ttl=60 * 10)
async def get_voice(url: str) -> BytesIO:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return BytesIO(response.content)


async def register_cost(voice_task: VoiceConvert):
    try:
        duration = voice_task.meta_data.get("duration", 0)
        price = Settings.minutes_price * duration
        usage = await finance.meter_cost(voice_task.user_id, amount=price)
        if usage:
            return usage
    except Exception as e:
        logging.error(f"Error registering cost. {voice_task.user_id} {voice_task.uid} {e}")

    logging.error(f"Insufficient balance. {voice_task.user_id} {voice_task.id}")
    await voice_task.fail("Insufficient balance.")


async def convert_voice(voice_task: VoiceConvert, **kwargs):
    duration = voice.get_duration(await get_voice(voice_task.url))
    voice_task.meta_data = (voice_task.meta_data or {}) | (
        {
            "duration": duration,
        }
    )
    usage = await register_cost(voice_task)

    if usage is None:
        return

    model = await VoiceModel.get_by_slug(voice_task.target_voice)
    voice_task.meta_data.update(
        {
            "model_name": model.name,
            "model_thumbnail": model.thumbnail,
        }
    )

    if not model:
        await voice_task.fail("Model not found.")
        return

    if voice_task.pitch_difference is None:
        voice_task._status = VoiceConvertStatus.pitch_conversion
        await voice_task.save()

        pitch_data = voice.get_voice_pitch_parselmouth(await get_voice(voice_task.url))
        voice_task.pitch_difference = voice.calculate_pitch_shift_log(
            pitch_data["robust_average"], model.base_pitch
        )

    run_id = voice.create_rvc_conversion_runpod(
        voice_task.url,
        model.model_url,
        voice_task.pitch_difference,
        voice_task.item_webhook_url,
    )

    voice_task._status = VoiceConvertStatus.voice_change
    voice_task.run_id = run_id
    await voice_task.save()


async def process_convert_voice_webhook(
    voice_task: VoiceConvert, data: PredictionModelWebhookData | RunpodWebhookData
):
    if isinstance(data, PredictionModelWebhookData):
        if voice_task.status == VoiceConvertStatus.voice_change:
            output_url = await media.upload_file(
                data.output,
                file_name=f"{voice_task.target_voice}.wav",
                user_id=voice_task.user_id,
            )
    else:
        output_url = data.output_url

    voice_task._status = VoiceConvertStatus.completed
    voice_task.output_url = output_url
    await voice_task.save()

    if voice_task.webhook_url:
        async with httpx.AsyncClient() as client:
            await client.post(
                voice_task.webhook_url,
                json=voice_task.model_dump(mode="json"),
            )


async def check_open_voice_convert_status(voice_task: VoiceConvert):
    pass
