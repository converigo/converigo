from pathlib import Path

from app.engines.base_engine import BaseEngine
from app.services.conversion_manager import register_engine


class ImageEngine(BaseEngine):
    ENGINE_NAME = "image"
    SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]

    async def convert(self, source_path: Path, target_format: str) -> Path:
        raise NotImplementedError("Image conversion is not implemented in this prototype.")


register_engine(ImageEngine)
