from pathlib import Path

from app.engines.base_engine import BaseEngine


class AudioEngine(BaseEngine):
    ENGINE_NAME = "audio"
    SUPPORTED_FORMATS = [
        "mp3",
        "wav",
        "aac",
        "flac",
        "ogg",
    ]

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        raise NotImplementedError(
            "Audio conversion is not implemented in this prototype."
        )