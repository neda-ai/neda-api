from fastapi_mongo_base.models import OwnedEntity

from .schemas import VoiceConvertStatus, VoiceConvertTaskSchema


class VoiceConvert(VoiceConvertTaskSchema, OwnedEntity):
    class Settings:
        indexes = OwnedEntity.Settings.indexes

    async def start_processing(self, **kwargs):
        from .services import convert_voice

        return await convert_voice(self, **kwargs)

    async def fail(self, reason: str):
        self.status = VoiceConvertStatus.error
        await self.save_report(reason, log_type="error")

    async def success(self, **kwargs):
        pass
