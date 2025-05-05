import uuid

import fastapi
from fastapi import BackgroundTasks
from fastapi_mongo_base.routes import AbstractTaskRouter
from fastapi_mongo_base.core import exceptions
from usso.fastapi import jwt_access_security

from .models import VoiceConvert
from .schemas import (
    PredictionModelWebhookData,
    RunpodWebhookData,
    VoiceConvertTaskCreateSchema,
    VoiceConvertTaskSchema,
)
from .services import process_convert_voice_webhook


class VoiceConvertRouter(AbstractTaskRouter[VoiceConvert, VoiceConvertTaskSchema]):
    def __init__(self):
        super().__init__(
            model=VoiceConvert,
            schema=VoiceConvertTaskSchema,
            user_dependency=jwt_access_security,
            prefix="/voices",
            draftable=False,
        )

    def config_routes(self, **kwargs):
        super().config_routes(update_route=False)

    async def retrieve_item(
        self,
        request: fastapi.Request,
        uid: uuid.UUID,
    ):
        user = await self.get_user(request)
        is_admin = "admin" in user.data.get("scopes", [])
        if is_admin:
            item = await self.get_item(uid, ignore_user_id=True)
        else:
            item = await self.get_item(uid, user_id=user.uid)
        return item

    async def create_item(
        self,
        request: fastapi.Request,
        data: VoiceConvertTaskCreateSchema,
        background_tasks: BackgroundTasks,
        # user_id: uuid.UUID | None = fastapi.Body(
        #     default=None,
        #     embed=True,
        #     description="Request for another User ID. It is possible only if the request user is admin. If not provided, the request user will be used.",
        # ),
    ):
        user = await self.get_user(request)
        is_admin = "admin" in user.data.get("scopes", [])
        # import logging
        # logging.info(f"user_id: {user_id} is_admin: {is_admin} user.uid: {user.uid}")

        # if user_id and not is_admin and user_id != user.uid:
        #     raise exceptions.BaseHTTPException(
        #         status_code=403,
        #         error="Forbidden",
        #         message={
        #             "en": "You are not allowed to request another user's ID.",
        #             "fa": "شما مجوز دسترسی به آیدی کاربر دیگری را ندارید.",
        #         },
        #     )

        user_id = user.uid
        item = await self.model.create_item({**data.model_dump(), "user_id": user_id})

        if item.task_status == "init" or not self.draftable:
            background_tasks.add_task(item.start_processing)
        return item

    async def webhook(
        self,
        uid: uuid.UUID,
        request: fastapi.Request,
        data: PredictionModelWebhookData | RunpodWebhookData,
    ):
        voice_task = await VoiceConvert.get_by_uid(uid)
        await process_convert_voice_webhook(voice_task, data)
        return {"message": "Webhook received"}


router = VoiceConvertRouter().router


@router.post("/pitch")
async def get_pitch(url: str = fastapi.Body(..., embed=True)):
    from utils import voice
    from .services import get_voice

    pitch_data = voice.get_voice_pitch_parselmouth(await get_voice(url))
    return pitch_data
