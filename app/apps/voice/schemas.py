from typing import Literal

from fastapi_mongo_base.schemas import OwnedEntitySchema


class VoiceTrainingSchema(OwnedEntitySchema):
    training_data: str


class VoiceModelSchema(OwnedEntitySchema):
    name: str
    slug: str
    model_url: str
    base_pitch: float = 0

    category: str | None = None
    gender: Literal["male", "female"] = "male"
