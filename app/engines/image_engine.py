"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 2.1.0

Image Engine
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.engines.base_engine import BaseEngine


class ImageEngine(BaseEngine):

    ENGINE_NAME = "image"

    SUPPORTED_FORMATS = [
        "jpg",
        "jpeg",
        "png",
        "gif",
        "bmp",
        "tiff",
        "webp",
        "ico",
    ]

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        target = target_format.lower().lstrip(".")

        if target not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported target format: {target}"
            )

        output_dir = Path("outputs") / "image"

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = output_dir / (
            f"{source_path.stem}.{target}"
        )

        suffix = source_path.suffix.lower()
        if suffix == ".svg":
            return self._convert_svg_to_png(source_path, output_path)

        self._load_optional_raster_backends(suffix)

        with Image.open(source_path) as image:

            if target in (
                "jpg",
                "jpeg",
            ):

                if image.mode in (
                    "RGBA",
                    "LA",
                    "P",
                ):
                    image = image.convert("RGB")

                image.save(
                    output_path,
                    quality=95,
                )

            elif target == "ico":

                if image.mode not in (
                    "RGB",
                    "RGBA",
                ):
                    image = image.convert("RGBA")

                image.thumbnail(
                    (
                        256,
                        256,
                    ),
                    Image.LANCZOS,
                )

                image.save(
                    output_path,
                    format="ICO",
                )

            else:

                image.save(
                    output_path,
                )

        return output_path

    def _load_optional_raster_backends(self, suffix: str) -> None:
        if suffix in {".heic", ".heif"}:
            try:
                import pillow_heif

                if hasattr(pillow_heif, "register_heif_opener"):
                    pillow_heif.register_heif_opener()
            except ImportError:
                pass

        if suffix == ".avif":
            try:
                import pillow_avif
            except ImportError:
                pass

    def _convert_svg_to_png(
        self,
        source_path: Path,
        output_path: Path,
    ) -> Path:
        try:
            import cairosvg
        except (ImportError, OSError) as exc:
            raise RuntimeError(
                "cairosvg and its native Cairo dependencies are required for SVG to PNG conversion."
            ) from exc

        try:
            cairosvg.svg2png(
                url=str(source_path),
                write_to=str(output_path),
            )
        except Exception as exc:
            raise RuntimeError(
                f"SVG to PNG conversion failed: {exc}"
            ) from exc

        if not output_path.exists():
            raise RuntimeError("SVG to PNG conversion did not produce output.")

        return output_path