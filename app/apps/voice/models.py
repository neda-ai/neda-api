from fastapi_mongo_base.models import OwnedEntity
from pymongo import ASCENDING, IndexModel

from .schemas import VoiceModelSchema


class VoiceModel(VoiceModelSchema, OwnedEntity):
    class Settings:
        indexes = OwnedEntity.Settings.indexes + [
            IndexModel([("slug", ASCENDING)], unique=True),
        ]

    @classmethod
    async def get_by_slug(cls, slug: str = "default"):
        return await cls.find_one({"slug": slug})
