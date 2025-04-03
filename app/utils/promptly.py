import os

import httpx
from fastapi_mongo_base.utils import basic


class PromptlyClient(httpx.AsyncClient):

    def __init__(self):
        super().__init__(
            base_url=os.getenv("PROMPTLY_URL"),
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "x-api-key": os.getenv("UFILES_API_KEY"),
            },
        )

    @basic.try_except_wrapper
    @basic.retry_execution(attempts=3, delay=1)
    async def ai_image(
        self, image_url: str, key: str, data: dict = {}, **kwargs
    ) -> dict:
        timeout = httpx.Timeout(kwargs.get("timeout", 30), read=None, connect=None)
        r = await self.post(
            f"/image/{key}",
            json={**data, "image_url": image_url},
            timeout=timeout,
            **kwargs,
        )
        r.raise_for_status()
        return r.json()

    @basic.try_except_wrapper
    @basic.retry_execution(attempts=3, delay=1)
    async def ai(self, key: str, data: dict = {}, **kwargs) -> dict:
        timeout = httpx.Timeout(kwargs.get("timeout", 30), read=None, connect=None)
        r = await self.post(f"/{key}", json=data, timeout=timeout, **kwargs)
        r.raise_for_status()
        return r.json()

    async def ai_search(self, key: str, data: dict = {}, **kwargs) -> dict:
        timeout = httpx.Timeout(kwargs.get("timeout", 30), read=None, connect=None)
        return await self.ai(f"/search/{key}", data, timeout=timeout, **kwargs)
