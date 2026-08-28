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
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        # Default audio engine is a prototype; ensure signature accepts
        # request-local output_dir and temp_dir so plugins can forward them.
        raise NotImplementedError(
            "Audio conversion is not implemented in this prototype."
        )