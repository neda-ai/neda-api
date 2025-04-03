from enum import Enum

from fastapi_mongo_base.schemas import OwnedEntitySchema
from fastapi_mongo_base.tasks import TaskMixin, TaskStatusEnum
from pydantic import BaseModel, field_validator


class VoiceConvertStatus(str, Enum):
    draft = "draft"
    queued = "queued"
    init = "init"
    pitch_conversion = "pitch_conversion"
    voice_change = "voice_change"
    done = "done"
    error = "error"
    no_speech = "no_speech"

    def get_task_status(self) -> TaskStatusEnum:
        return {
            self.draft: TaskStatusEnum.draft,
            self.init: TaskStatusEnum.init,
            self.pitch_conversion: TaskStatusEnum.processing,
            self.voice_change: TaskStatusEnum.processing,
            self.done: TaskStatusEnum.done,
            self.error: TaskStatusEnum.error,
            self.no_speech: TaskStatusEnum.error,
        }[self]


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

    _status: VoiceConvertStatus = VoiceConvertStatus.draft

    transcription_job_id: str | None = None
    subtitled_url: str | None = None

    @property
    def status(self) -> VoiceConvertStatus:
        return self._status

    @status.setter
    def status(self, value: VoiceConvertStatus | str):
        if isinstance(value, str):
            value = VoiceConvertStatus(value)
        self._status = value
        self.task_status = value.get_task_status()

    @property
    def filename(self):
        from pathlib import Path
        from urllib.parse import urlparse

        return Path(urlparse(self.url).path).stem
