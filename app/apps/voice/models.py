from fastapi_mongo_base.models import OwnedEntity
from pymongo import ASCENDING, IndexModel

from .schemas import VoiceModelSchema


class VoiceModel(VoiceModelSchema, OwnedEntity):
    class Settings:
        indexes = OwnedEntity.Settings.indexes + [
            IndexModel([("name", ASCENDING)], unique=True),
        ]
