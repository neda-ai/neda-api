from fastapi_mongo_base.models import OwnedEntity

from .schemas import VoiceConvertTaskSchema


class VoiceConvert(VoiceConvertTaskSchema, OwnedEntity):
    class Settings:
        indexes = OwnedEntity.Settings.indexes

    async def start_processing(self, **kwargs):
        from .services import convert_voice

        return await convert_voice(self, **kwargs)
