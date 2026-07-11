"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 2.0.0
"""

import asyncio
from pathlib import Path

from app.core.settings import settings
from app.plugins.registry import registry


class ConversionError(Exception):
    pass


class ConversionService:

    async def convert_file(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        source_format = source_path.suffix.replace(".", "")

        plugin = registry.get_plugin(
            source_format,
            target_format,
        )

        timeout_seconds = self._get_timeout_seconds(source_format, target_format)

        try:
            output_path = await asyncio.wait_for(
                plugin.convert(source_path, target_format),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise ConversionError(
                f"Conversion timed out after {timeout_seconds} seconds."
            ) from exc
        except (RuntimeError, ValueError) as exc:
            raise ConversionError(str(exc)) from exc

        if not output_path.exists():

            raise ConversionError(
                "Converted file was not saved."
            )

        return output_path

    def _get_timeout_seconds(self, source_format: str, target_format: str) -> int:
        if source_format in {"mp4", "mov", "avi", "mkv", "webm"}:
            return settings.VIDEO_CONVERSION_TIMEOUT_SECONDS
        if source_format in {"mp3", "wav", "aac", "ogg", "flac", "m4a"}:
            return settings.AUDIO_CONVERSION_TIMEOUT_SECONDS
        if source_format in {"jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "ico"}:
            return settings.IMAGE_CONVERSION_TIMEOUT_SECONDS
        if source_format in {"pdf", "docx", "doc", "txt", "md"}:
            return settings.DOCUMENT_CONVERSION_TIMEOUT_SECONDS
        return settings.CONVERSION_TIMEOUT_SECONDS