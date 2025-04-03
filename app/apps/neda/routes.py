import fastapi
from fastapi import BackgroundTasks
from fastapi_mongo_base.routes import AbstractTaskRouter
from usso.fastapi import jwt_access_security

from .models import VoiceConvert
from .schemas import VoiceConvertTaskCreateSchema, VoiceConvertTaskSchema


class VoiceConvertRouter(AbstractTaskRouter[VoiceConvert, VoiceConvertTaskSchema]):
    def __init__(self):
        super().__init__(
            model=VoiceConvert,
            schema=VoiceConvertTaskSchema,
            user_dependency=jwt_access_security,
        )

    def config_routes(self, **kwargs):
        super().config_routes(update_route=False)

    async def create_item(
        self,
        request: fastapi.Request,
        data: VoiceConvertTaskCreateSchema,
        background_tasks: BackgroundTasks,
    ):
        return await super().create_item(request, data.model_dump(), background_tasks)


router = VoiceConvertRouter().router
