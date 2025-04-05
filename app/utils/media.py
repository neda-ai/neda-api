import json
import uuid
from io import BytesIO

import ufiles
from server.config import Settings


async def upload_file(
    file_url: str,
    file_name: str,
    user_id: uuid.UUID,
    file_upload_dir: str = "voices",
    meta_data: dict = {},
):
    ufiles_client = ufiles.AsyncUFiles(
        ufiles_base_url=Settings.UFILES_BASE_URL,
        usso_base_url=Settings.USSO_BASE_URL,
        api_key=Settings.UFILES_API_KEY,
    )
    ufile_item = await ufiles_client.upload_url(
        file_url,
        filename=f"{file_upload_dir}/{file_name}",
        public_permission=json.dumps({"permission": ufiles.PermissionEnum.READ}),
        user_id=str(user_id),
        meta_data=meta_data,
    )
    return ufile_item.url
