import os
import logging
import cloudinary
import cloudinary.uploader
from typing import List
from fastapi import UploadFile

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True,
)


async def upload_images(files: List[UploadFile], property_id: str) -> List[str]:
    """Upload images to Cloudinary and return list of secure_urls."""
    urls = []
    for idx, file in enumerate(files):
        logger.info(
            "[Cloudinary] Starting upload: file=%s property_id=%s index=%d",
            file.filename,
            property_id,
            idx,
        )
        try:
            contents = await file.read()
            public_id = f"easyfind_properties/{property_id}_{idx}"
            result = cloudinary.uploader.upload(
                contents,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
            )
            secure_url = result.get("secure_url", "")
            logger.info(
                "[Cloudinary] Upload success: public_id=%s url=%s",
                result.get("public_id"),
                secure_url,
            )
            urls.append(secure_url)
        except Exception as exc:
            logger.error(
                "[Cloudinary] Upload failed: file=%s error=%s",
                file.filename,
                str(exc),
            )
            raise RuntimeError(f"Cloudinary upload failed for {file.filename}: {exc}") from exc
    return urls
