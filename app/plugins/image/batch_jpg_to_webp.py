"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.1.0

Batch JPG to WEBP Plugin

Convert multiple JPG images to WEBP format and package them as a ZIP
archive.  Uses Pillow (MIT) for the actual conversion.
"""

import zipfile
from pathlib import Path
from typing import List

from PIL import Image

from app.plugins.base import ConverterPlugin


class BatchJPGToWEBPPlugin(ConverterPlugin):
    slug = "batch-jpg-to-webp"
    name = "Batch JPG to WEBP"
    description = "Convert multiple JPG images to WEBP and download as a ZIP."
    category = "image"
    engine = "image"
    icon = "🔄"

    source_formats = ["jpg", "jpeg"]
    target_formats = ["webp"]

    goal = "compress"
    use_case = "Best for bulk-converting JPGs to the smaller WEBP format for the web."
    priority = 77
    quality = 90
    compatibility = 90
    estimated_saving = 30
    badge = "Batch WEBP"
    seo_title = "Batch JPG to WEBP Converter | Converigo"
    seo_description = "Convert multiple JPG images to WEBP format in one go."

    def _convert_to_webp(self, source_path: Path, output_path: Path) -> None:
        """Convert a single JPG image to WEBP."""
        with Image.open(source_path) as image:
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")
            image.save(str(output_path), "WEBP", quality=80)

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("BatchJPGToWEBPPlugin only supports JPG/JPEG -> WEBP.")

        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "image")
        working_root.mkdir(parents=True, exist_ok=True)

        output_path = working_root / f"{source_path.stem}.webp"
        self._convert_to_webp(source_path, output_path)

        if not output_path.exists():
            raise RuntimeError("JPG to WEBP conversion did not produce output.")
        return output_path

    async def merge(
        self,
        source_paths: List[Path],
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "image")
        working_root.mkdir(parents=True, exist_ok=True)

        if len(source_paths) < 2:
            raise RuntimeError("batch-jpg-to-webp requires at least 2 JPG files.")

        zip_path = working_root / "batch_webp.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as archive:
            for path in source_paths:
                output_name = f"{path.stem}.webp"
                tmp_path = working_root / output_name
                self._convert_to_webp(path, tmp_path)
                archive.write(str(tmp_path), arcname=output_name)
                tmp_path.unlink(missing_ok=True)

        return zip_path