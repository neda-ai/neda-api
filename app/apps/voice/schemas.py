from fastapi_mongo_base.schemas import OwnedEntitySchema


class VoiceTrainingSchema(OwnedEntitySchema):
    training_data: str


class VoiceModelSchema(OwnedEntitySchema):
    name: str
    model_url: str
    base_pitch: float = 0
