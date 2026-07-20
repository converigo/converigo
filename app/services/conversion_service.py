"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 2.0.0
"""

import asyncio
from pathlib import Path

from app.core.settings import settings
from app.plugins.registry import registry
import logging

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    pass


class UnsupportedConversionError(Exception):
    def __init__(self, source_format: str, target_format: str, message: str | None = None) -> None:
        self.source_format = source_format
        self.target_format = target_format
        if message is None:
            message = f"{source_format.upper()} to {target_format.upper()} conversion is not supported yet"
        super().__init__(message)


class PDFEmptyError(UnsupportedConversionError):
    def __init__(
        self,
        source_format: str | None = None,
        target_format: str | None = None,
        message: str = "PDF has no pages",
    ) -> None:
        if source_format is None:
            source_format = "pdf"
        if target_format is None:
            target_format = "docx"
        super().__init__(source_format, target_format, message)


class PDFPasswordProtectedError(UnsupportedConversionError):
    def __init__(
        self,
        source_format: str | None = None,
        target_format: str | None = None,
        message: str = "PDF is password protected",
    ) -> None:
        if source_format is None:
            source_format = "pdf"
        if target_format is None:
            target_format = "docx"
        super().__init__(source_format, target_format, message)


class PDFValidationError(UnsupportedConversionError):
    def __init__(
        self,
        source_format: str | None = None,
        target_format: str | None = None,
        message: str = "PDF validation failed",
    ) -> None:
        if source_format is None:
            source_format = "pdf"
        if target_format is None:
            target_format = "docx"
        super().__init__(source_format, target_format, message)


class ConversionService:

    async def convert_file(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        source_format = source_path.suffix.replace(".", "").lower()
        target_format = target_format.lower().strip()

        try:
            plugin = registry.get_plugin(
                source_format,
                target_format,
            )
            try:
                slug = getattr(plugin, "slug", None)
            except Exception:
                slug = None
            logger.info("Selected plugin for conversion: %s (%s -> %s)", slug or str(plugin), source_format, target_format)
            # [CONVERTER_DEBUG] — plugin/engine/input/target
            engine_name = getattr(plugin, "engine", None)
            logger.info(
                "[CONVERTER_DEBUG] ConversionService selected plugin=%s engine=%s input=%s target=%s",
                slug or str(plugin),
                engine_name,
                str(source_path),
                target_format,
            )
        except ValueError as exc:
            raise UnsupportedConversionError(source_format, target_format) from exc

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
        except RuntimeError as exc:
            logger.exception("[CONVERTER_DEBUG] ConversionService runtime error during plugin.convert")
            raise ConversionError(str(exc)) from exc
        except UnsupportedConversionError:
            raise
        except ValueError as exc:
            message = str(exc)
            if message.startswith("Unsupported ") or "Unsupported" in message:
                raise UnsupportedConversionError(source_format, target_format) from exc
            logger.exception("[CONVERTER_DEBUG] ConversionService value error during plugin.convert")
            raise ConversionError(message) from exc
        except Exception as exc:
            logger.exception("[CONVERTER_DEBUG] ConversionService raised an unexpected exception")
            raise ConversionError(f"{type(exc).__name__}: {exc}") from exc

        logger.info("Plugin returned output path: %s", str(output_path))
        logger.info("[CONVERTER_DEBUG] ConversionService output_path=%s", str(output_path))

        if not isinstance(output_path, Path):
            raise ConversionError("Invalid output path.")

        resolved_output_path = output_path.resolve(strict=False)
        resolved_output_dir = settings.OUTPUT_DIR.resolve(strict=False)
        resolved_workdir = Path.cwd().resolve(strict=False)
        resolved_source_dir = source_path.resolve(strict=False).parent

        allowed_roots = {resolved_output_dir, resolved_workdir, resolved_source_dir}
        if not any(
            resolved_output_path == root or root in resolved_output_path.parents
            for root in allowed_roots
        ):
            raise ConversionError(
                f"Output path is outside the allowed output directory: {resolved_output_dir}"
            )

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