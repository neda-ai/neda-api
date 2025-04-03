from fastapi_mongo_base.core import app_factory

from apps.neda.routes import router as neda_router
from apps.voice.routes import router as voice_router

from . import config, worker

app = app_factory.create_app(settings=config.Settings(), worker=worker.worker)
app.include_router(neda_router, prefix=f"{config.Settings.base_path}")
app.include_router(voice_router, prefix=f"{config.Settings.base_path}")
