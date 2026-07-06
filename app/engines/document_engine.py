from pathlib import Path

from app.engines.base_engine import BaseEngine
from app.services.conversion_manager import register_engine


class DocumentEngine(BaseEngine):
    ENGINE_NAME = "document"
    SUPPORTED_FORMATS = ["pdf", "docx", "txt", "md"]

    async def convert(self, source_path: Path, target_format: str) -> Path:
        raise NotImplementedError("Document conversion is not implemented in this prototype.")


register_engine(DocumentEngine)
