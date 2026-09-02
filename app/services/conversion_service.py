"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 2.0.0
"""

import asyncio
import logging
import shutil
import uuid
from pathlib import Path

from app.core.settings import settings
from app.plugins.registry import registry

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
        conversion_id: str | None = None,
        plugin_slug: str | None = None,
    ) -> Path:

        source_format = source_path.suffix.replace(".", "").lower()
        target_format = target_format.lower().strip()
        conversion_id = conversion_id or uuid.uuid4().hex

        try:
            if plugin_slug is not None:
                plugin = registry.get_plugin(
                    source_format,
                    target_format,
                    slug=plugin_slug,
                )
            else:
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
        temp_root = settings.TEMP_DIR / conversion_id
        public_root = settings.OUTPUT_DIR / conversion_id
        temp_root.mkdir(parents=True, exist_ok=True)

        try:
            output_path = await asyncio.wait_for(
                plugin.convert(
                    source_path,
                    target_format,
                    output_dir=public_root,
                    temp_dir=temp_root,
                ),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            self._cleanup_temp_artifacts(temp_root)
            raise ConversionError(
                f"Conversion timed out after {timeout_seconds} seconds."
            ) from exc
        except RuntimeError as exc:
            self._cleanup_temp_artifacts(temp_root)
            logger.exception("[CONVERTER_DEBUG] ConversionService runtime error during plugin.convert")
            raise ConversionError(str(exc)) from exc
        except UnsupportedConversionError:
            self._cleanup_temp_artifacts(temp_root)
            raise
        except ValueError as exc:
            self._cleanup_temp_artifacts(temp_root)
            message = str(exc)
            if message.startswith("Unsupported ") or "Unsupported" in message:
                raise UnsupportedConversionError(source_format, target_format) from exc
            logger.exception("[CONVERTER_DEBUG] ConversionService value error during plugin.convert")
            raise ConversionError(message) from exc
        except Exception as exc:
            self._cleanup_temp_artifacts(temp_root)
            logger.exception("[CONVERTER_DEBUG] ConversionService raised an unexpected exception")
            raise ConversionError(f"{type(exc).__name__}: {exc}") from exc
        logger.info("Plugin returned output path: %s", str(output_path))
        logger.info("[CONVERTER_DEBUG] ConversionService output_path=%s", str(output_path))

        if not isinstance(output_path, Path):
            self._cleanup_temp_artifacts(temp_root)
            raise ConversionError("Invalid output path.")

        output_path = output_path.resolve(strict=False)
        public_output_path = self._publish_output(output_path, public_root, temp_root, conversion_id=conversion_id)

        resolved_output_path = public_output_path.resolve(strict=False)
        resolved_public_root = public_root.resolve(strict=False)
        resolved_workdir = Path.cwd().resolve(strict=False)
        resolved_source_dir = source_path.resolve(strict=False).parent

        allowed_roots = {resolved_public_root, resolved_workdir, resolved_source_dir}
        if not any(
            resolved_output_path == root or root in resolved_output_path.parents
            for root in allowed_roots
        ):
            raise ConversionError(
                f"Output path is outside the allowed output directory: {resolved_public_root}"
            )

        if not public_output_path.exists():
            raise ConversionError(
                "Converted file was not saved."
            )

        return public_output_path

    async def merge_files(
        self,
        source_paths: list[Path],
        conversion_id: str | None = None,
        plugin_slug: str | None = None,
    ) -> Path:
        """Merge multiple PDF files into one output file.

        Uses the PDFMergePlugin's ``merge()`` method under the hood.
        Validates the output and publishes it under the conversion ID.
        """
        source_format = "pdf"
        target_format = "pdf"
        conversion_id = conversion_id or uuid.uuid4().hex

        plugin = registry.get_plugin(source_format, target_format, slug=plugin_slug)

        timeout_seconds = self._get_timeout_seconds(source_format, target_format)
        temp_root = self._build_temp_root(conversion_id)
        public_root = settings.OUTPUT_DIR / conversion_id
        public_root.mkdir(parents=True, exist_ok=True)

        try:
            output_path = await asyncio.wait_for(
                plugin.merge(
                    source_paths,
                    output_dir=public_root,
                    temp_dir=temp_root,
                ),
                timeout=timeout_seconds,
            )
        except Exception as exc:
            self._cleanup_temp_artifacts(temp_root, conversion_id=conversion_id)
            raise ConversionError(str(exc)) from exc

        logger.info("Plugin returned output path: %s", str(output_path))

        if not isinstance(output_path, Path):
            self._cleanup_temp_artifacts(temp_root)
            raise ConversionError("Invalid output path.")

        output_path = output_path.resolve(strict=False)
        public_output_path = self._publish_output(output_path, public_root, temp_root, conversion_id=conversion_id)

        if not public_output_path.exists():
            raise ConversionError("Converted file was not saved.")

        return public_output_path

    def _build_temp_root(self, conversion_id: str) -> Path:
        temp_root = settings.TEMP_DIR / conversion_id
        temp_root.mkdir(parents=True, exist_ok=True)
        return temp_root

    def _publish_output(
        self,
        output_path: Path,
        public_root: Path,
        temp_root: Path,
        conversion_id: str | None = None,
    ) -> Path:
        if not output_path.exists():
            self._cleanup_temp_artifacts(temp_root, conversion_id=conversion_id)
            raise ConversionError("Converted file was not saved.")

        public_root.mkdir(parents=True, exist_ok=True)
        public_output_path = public_root / output_path.name

        output_path_abs = output_path.resolve(strict=False)
        public_output_path_abs = public_output_path.resolve(strict=False)
        if output_path_abs == public_output_path_abs:
            return public_output_path

        if public_output_path.exists():
            public_output_path.unlink(missing_ok=True)
        shutil.move(str(output_path), str(public_output_path))

        self._cleanup_temp_artifacts(temp_root, conversion_id=conversion_id)
        return public_output_path

    def _cleanup_temp_artifacts(self, temp_root: Path, conversion_id: str | None = None) -> None:
        if not temp_root.exists():
            return
        try:
            shutil.rmtree(temp_root, ignore_errors=True)
        except Exception:
            logger.exception("Failed to remove temporary conversion artifacts: %s", temp_root)

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