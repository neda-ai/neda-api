from datetime import datetime
from enum import Enum

from fastapi_mongo_base.schemas import OwnedEntitySchema
from fastapi_mongo_base.tasks import TaskMixin, TaskStatusEnum
from pydantic import BaseModel, field_validator, model_validator


class VoiceConvertStatus(str, Enum):
    draft = "draft"
    queued = "queued"
    init = "init"
    pitch_conversion = "pitch_conversion"
    voice_change = "voice_change"
    completed = "completed"
    error = "error"
    no_speech = "no_speech"

    def get_task_status(self) -> TaskStatusEnum:
        return {
            self.draft: TaskStatusEnum.draft,
            self.init: TaskStatusEnum.init,
            self.pitch_conversion: TaskStatusEnum.processing,
            self.voice_change: TaskStatusEnum.processing,
            self.completed: TaskStatusEnum.completed,
            self.error: TaskStatusEnum.error,
            self.no_speech: TaskStatusEnum.error,
        }[self]

    @classmethod
    def from_replicate(cls, status: str):
        return {
            "init": cls.init,
            "processing": cls.voice_change,
            "succeeded": cls.completed,
            "completed": cls.completed,
            "error": cls.error,
        }.get(status, cls.error)

    @property
    def progress(self):
        return {
            self.__class__.pitch_conversion: 50,
            self.__class__.voice_change: 100,
        }.get(self, 0)


class VoiceConvertTaskCreateSchema(BaseModel):
    url: str
    pitch_difference: float = 0.0
    target_voice: str

    meta_data: dict | None = None
    webhook_url: str | None = None

    @field_validator("url")
    def validate_url(cls, v: str):
        if not v or not v.startswith("http"):
            raise ValueError("URL is required")
        return v.strip()


class VoiceConvertTaskSchema(
    VoiceConvertTaskCreateSchema, TaskMixin, OwnedEntitySchema
):
    estimated_cost: float | None = None

    status: VoiceConvertStatus = VoiceConvertStatus.draft
    replicate_id: str | None = None
    output_url: str | None = None

    @property
    def item_url(self):
        from server.config import Settings

        return f"https://{Settings.root_url}{Settings.base_path}/voices/{self.uid}"

    @property
    def _status(self) -> VoiceConvertStatus:
        return self.status

    @_status.setter
    def _status(self, value: VoiceConvertStatus | str):
        if isinstance(value, str):
            value = VoiceConvertStatus(value)
        self.status = value
        self.task_status = value.get_task_status()

    @property
    def filename(self):
        from pathlib import Path
        from urllib.parse import urlparse

        return Path(urlparse(self.url).path).stem


class PredictionModelWebhookData(BaseModel):
    completed_at: datetime | None = None
    created_at: datetime
    data_removed: bool = False
    error: str | None = None
    id: str
    input: dict | None = None
    logs: str | None = None
    metrics: dict | None = None
    model: str
    output: str | list[str] | None = None
    started_at: datetime | None = None
    status: VoiceConvertStatus
    percentage: int = 0
    urls: dict[str, str] | None = None
    version: str
    webhook: str | None = None
    webhook_events_filter: list[str] | None = None

    @field_validator("status", mode="before")
    def validate_status(cls, value):
        return VoiceConvertStatus.from_replicate(value)

    @model_validator(mode="after")
    def validate_percentage(cls, item: "PredictionModelWebhookData"):
        item.percentage = item.status.progress
        return item


class VoiceInput(BaseModel):
    custom_rvc_model_download_url: str
    filter_radius: int
    index_rate: float
    input_audio: str
    output_format: str
    pitch_change: int
    protect: float
    rms_mix_rate: float
    rvc_model: str


class Urls(BaseModel):
    cancel: str
    get: str
    stream: str


class Metrics(BaseModel):
    predict_time: float


class VoiceWebhookResponse(BaseModel):
    completed_at: datetime
    created_at: datetime
    data_removed: bool
    error: str | None = None
    id: str
    input: VoiceInput
    logs: str
    metrics: Metrics
    model: str
    output: str
    started_at: datetime
    status: str
    urls: Urls
    version: str
    webhook: str
    webhook_events_filter: list[str] | None = None
