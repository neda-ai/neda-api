import fastapi
from fastapi_mongo_base.routes import AbstractBaseRouter

from .models import VoiceModel
from .schemas import VoiceModelSchema, VoiceTrainingSchema


class VoiceModelRouter(AbstractBaseRouter[VoiceModel, VoiceModelSchema]):
    def __init__(self):
        super().__init__(
            model=VoiceModel,
            schema=VoiceModelSchema,
            user_dependency=None,
            prefix="/models",
        )

    def config_routes(self, **kwargs):
        super().config_routes()
        self.router.add_route("/train", self.train_item, methods=["POST"])

    async def create_item(
        self,
        request: fastapi.Request,
        data: VoiceModelSchema,
    ):
        return await super().create_item(request, data.model_dump())

    async def update_item(
        self,
        request: fastapi.Request,
        data: VoiceModelSchema,
    ):
        return await super().update_item(request, data.model_dump())

    async def train_item(
        self,
        request: fastapi.Request,
        data: VoiceTrainingSchema,
    ):
        raise NotImplementedError


router = VoiceModelRouter().router
