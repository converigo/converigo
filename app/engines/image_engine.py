"""
Project : Convertin
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