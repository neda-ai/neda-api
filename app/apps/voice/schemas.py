from typing import Literal

from fastapi_mongo_base.schemas import OwnedEntitySchema


class VoiceTrainingSchema(OwnedEntitySchema):
    training_data: str


class VoiceModelSchema(OwnedEntitySchema):
    name: str
    slug: str
    model_url: str
    base_pitch: float = 0
    thumbnail: str | None = (
        "https://media.pixy.ir/v1/f/5bf5d94c-60ef-454f-9846-2c29064e19f6/download.png"
    )
    sample_voice: str | None = None

    category: str | None = None
    gender: Literal["male", "female"] = "male"
