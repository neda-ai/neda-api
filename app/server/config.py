"""FastAPI server configuration."""

import dataclasses
import os
from pathlib import Path

import dotenv
from fastapi_mongo_base.core import config

dotenv.load_dotenv()


@dataclasses.dataclass
class Settings(config.Settings):
    base_dir: Path = Path(__file__).resolve().parent.parent
    base_path: str = "/v1/apps/neda"
    update_time: int = 10

    UFILES_API_KEY: str = os.getenv("UFILES_API_KEY")
    UFILES_BASE_URL: str = os.getenv("UFILES_URL", default="https://media.pixiee.io/v1")
    USSO_BASE_URL: str = os.getenv("USSO_URL", default="https://sso.pixiee.io")
    UFAAS_BASE_URL: str = os.getenv(
        "UFAAS_BASE_URL", default="https://wallet.pixiee.io"
    )
    UFAAS_RESOURCE_VARIANT: str = os.getenv("UFAAS_RESOURCE_VARIANT", default="neda")
    PROMPTLY_URL: str = os.getenv(
        "PROMPTLY_URL", default="https://media.pixiee.io/v1/apps/promptly/ai"
    )
    minutes_price: float = 3  # coin per minute
    translation_price: float = (
        2.25  # coins per minute (K tokens) 1.5 output + 0.75 input
    )
