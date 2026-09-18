"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.1.0

Image Compress Plugin

Lossy image compression for JPG/JPEG using Pillow (MIT).
Re-encodes at a lower quality to reduce file size.
"""

from pathlib import Path

from PIL import Image

from app.plugins.base import ConverterPlugin


class ImageCompressPlugin(ConverterPlugin):
    slug = "image-compress"
    name = "Image Compress"
    description = "Compress JPG/JPEG images to reduce file size (lossy)."
    category = "image"
    engine = "image"
    icon = "🗜️"

    source_formats = ["jpg", "jpeg"]
    target_formats = ["jpg", "jpeg"]

    goal = "compress"
    use_case = "Best for shrinking JPG file size for faster uploads and lighter storage."
    priority = 78
    quality = 85
    compatibility = 90
    estimated_saving = 40
    badge = "Smaller Files"
    seo_title = "Image Compress Converter | Converigo"
    seo_description = "Compress JPG and JPEG images to reduce file size while keeping quality."

    def registration_pairs(self) -> list[tuple[str, str]]:
        """Register only the same-format diagonal (jpg->jpg, jpeg->jpeg).

        The default cross product would leak the alias pair jpg -> jpeg into
        the registry-derived dropdown map; compression preserves the source
        format, so this keeps registration aligned with the shipped map (the
        same guard ImageResizePlugin uses).
        """
        return [(fmt.lower(), fmt.lower()) for fmt in self.source_formats]

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("ImageCompressPlugin only supports JPG/JPEG -> JPG/JPEG.")

        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "image")
        working_root.mkdir(parents=True, exist_ok=True)

        output_path = working_root / f"{source_path.stem}_compressed.{target_format}"
        with Image.open(source_path) as image:
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")
            image.save(str(output_path), "JPEG", quality=65, optimize=True)

        if not output_path.exists():
            raise RuntimeError("Image compress did not produce output.")
        return output_path