"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.1.0

Image Resize Plugin

Batch resize images using Pillow (MIT). Supports single-file and
multi-file (batch -> ZIP) modes.  The resize preserves the source
format and reduces the longest dimension to a configurable maximum.
"""

import zipfile
from pathlib import Path
from typing import List

from PIL import Image

from app.plugins.base import ConverterPlugin


class ImageResizePlugin(ConverterPlugin):
    slug = "image-resize"
    name = "Image Resize"
    description = "Resize images to reduce dimensions while preserving quality."
    category = "image"
    engine = "image"
    icon = "📐"

    source_formats = ["jpg", "jpeg", "png", "webp", "bmp", "tiff"]
    target_formats = ["jpg", "jpeg", "png", "webp", "bmp", "tiff"]

    goal = "resize"
    use_case = "Best for resizing images for web, email, or social media."
    priority = 77
    quality = 90
    compatibility = 90
    estimated_saving = 20
    badge = "Resize"
    seo_title = "Image Resize Converter | Converigo"
    seo_description = "Resize images quickly and easily with our online converter."

    MAX_DIMENSION = 800  # longest side in pixels

    def supports(self, source_format: str, target_format: str) -> bool:
        source = source_format.lower().replace(".", "")
        target = target_format.lower().replace(".", "")
        return (
            source in self.source_formats
            and target in self.target_formats
            and source == target  # resize preserves format
        )

    def registration_pairs(self) -> list[tuple[str, str]]:
        """Register only the same-format diagonal (jpg->jpg, png->png, ...).

        The default cross product would leak unsupported pairs (e.g.
        jpg -> bmp) into the registry-derived dropdown map and silently
        shadow dedicated format converters in the legacy pair index.
        This keeps registration aligned with supports().
        """
        return [(fmt.lower(), fmt.lower()) for fmt in self.source_formats]

    def _resize_image(self, source_path: Path, output_path: Path) -> None:
        """Resize a single image to MAX_DIMENSION on the longest side."""
        with Image.open(source_path) as image:
            orig_w, orig_h = image.size
            if max(orig_w, orig_h) <= self.MAX_DIMENSION:
                # Already small enough — just copy and return.
                image.save(str(output_path))
                return

            if orig_w >= orig_h:
                new_w = self.MAX_DIMENSION
                new_h = int(orig_h * (self.MAX_DIMENSION / orig_w))
            else:
                new_h = self.MAX_DIMENSION
                new_w = int(orig_w * (self.MAX_DIMENSION / orig_h))

            resized = image.resize((new_w, new_h), Image.LANCZOS)
            if image.mode in ("RGBA", "LA", "P"):
                resized = resized.convert("RGB")

            ext = output_path.suffix.lower().lstrip(".")
            save_format = "JPEG" if ext in ("jpg", "jpeg") else ext.upper()
            resized.save(str(output_path), format=save_format)

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("ImageResizePlugin only supports same-format resize.")

        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "image")
        working_root.mkdir(parents=True, exist_ok=True)

        ext = Path(source_path.suffix.lower().lstrip(".") or "jpg")
        output_path = working_root / f"{source_path.stem}_resized.{ext}"
        self._resize_image(source_path, output_path)

        if not output_path.exists():
            raise RuntimeError("Image resize did not produce output.")
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
            raise RuntimeError("image-resize batch requires at least 2 images.")

        zip_path = working_root / "resized_batch.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as archive:
            for path in source_paths:
                output_name = f"{path.stem}_resized{path.suffix}"
                tmp_path = working_root / output_name
                self._resize_image(path, tmp_path)
                archive.write(str(tmp_path), arcname=output_name)
                tmp_path.unlink(missing_ok=True)

        return zip_path