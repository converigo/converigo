"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.1.0

Images to PDF Plugin (VAR-10 / Batch 3)

Combine multiple images into a single PDF using Pillow (HPND/MIT-CMU).
Multi-file operation; requires at least 2 images. A single image is
handled honestly by convert() as a one-page PDF (same genuine pipeline).
"""

from pathlib import Path
from typing import List

from PIL import Image

from app.plugins.base import ConverterPlugin


class ImagesToPDFPlugin(ConverterPlugin):
    slug = "images-to-pdf"
    name = "Images to PDF"
    description = "Combine multiple images into a single PDF document."
    category = "image"
    engine = "image"
    icon = "🖼️"

    # jpg/jpeg are intentionally excluded here: JPG -> PDF is already served
    # by the dedicated jpg-to-pdf plugin (registered on the same pair).
    source_formats = ["png", "webp", "bmp", "tiff", "gif"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for turning a batch of images into one portable PDF."
    priority = 78
    quality = 88
    compatibility = 85
    estimated_saving = 15
    badge = "Images to PDF"
    seo_title = "Images to PDF Converter | Converigo"
    seo_description = "Combine multiple images into one PDF document easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        """Single-image path: embed one image as a genuine one-page PDF."""
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("ImagesToPDFPlugin only supports png/webp/bmp/tiff/gif -> PDF.")

        return await self._combine(
            [source_path],
            output_dir=output_dir,
            temp_dir=temp_dir,
            min_count=1,
        )

    async def merge(
        self,
        source_paths: List[Path],
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        """Multi-file operation: combine at least 2 images into one PDF."""
        return await self._combine(
            source_paths,
            output_dir=output_dir,
            temp_dir=temp_dir,
            min_count=2,
        )

    async def _combine(
        self,
        source_paths: List[Path],
        output_dir: Path | None,
        temp_dir: Path | None,
        min_count: int,
    ) -> Path:
        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "image")
        working_root.mkdir(parents=True, exist_ok=True)

        if len(source_paths) < min_count:
            raise RuntimeError("images-to-pdf requires at least 2 images.")

        images = []
        try:
            for path in source_paths:
                img = Image.open(path)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                images.append(img)

            if len(images) == 1:
                output_path = working_root / f"{source_paths[0].stem}.pdf"
            else:
                output_path = working_root / "combined.pdf"

            images[0].save(
                str(output_path),
                "PDF",
                save_all=True,
                append_images=images[1:],
                resolution=150,
            )
        finally:
            for img in images:
                img.close()

        if not output_path.exists():
            raise RuntimeError("Images to PDF conversion did not produce output.")
        return output_path