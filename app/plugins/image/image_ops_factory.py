"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F2)
Version : 1.0.0

Image Ops Factory Batch F2 - cluster G-B (Image Operations, net-new).

Nine thin converters built on the F0 certified factory scaffolding
(app/factory/plugin_base.py): discovery -> supports() check -> working
root -> single servable file -> non-empty output -> honest RuntimeError
-> API 422 UNSUPPORTED_CONVERSION.

Supervisor decisions applied (F2 audit: tmp/f2_image_ops_audit.md):
- D1: crop/watermark use FIXED semantics (center 80% crop / "CONVERIGO"
  text stamp).  No options channel; parameterization deferred to a
  future upgrade batch if demand appears.
- D2: Base64 <-> Image (VAR-39/40) deferred to a separate cluster audit.
- D3: watermark font = Pillow built-in ImageFont.load_default(size=...)
  (Pillow >= 10.1); zero new dependencies or bundled assets.
- D4: operation slug convention <format>-<operation>; one slug per op
  per format (jpg-rotate, jpg-flip, jpg-grayscale, jpg-compress,
  png-compress, jpg-crop, jpg-watermark).

Self-pair note (registry): the six jpg-* operations intentionally share
the (jpg, jpg) pair, exactly like the pdf-compress / pdf-split
precedent.  The registry pair index keeps a single deterministic legacy
entry while every operation is resolved through its unique operation
slug (registry.get_plugin(..., slug=...)); self-pairs are excluded from
the STATIC_TARGET_MAP dropdown, so no operation overwrites another in
any routed path.

Engine reuse (zero new dependencies): Pillow 12 (BSD-3-Clause) for all
pixel operations, pillow-heif (already required) for HEIC decode.
DecompressionBombError and undecodable inputs are mapped to RuntimeError
so the API boundary keeps answering with the honest 422
UNSUPPORTED_CONVERSION error class instead of a 500.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.factory import make_plugin_class

#: Fixed watermark text (D1/D3): Pillow built-in font, semi-transparent.
_WATERMARK_TEXT = "CONVERIGO"

#: Fixed recompression quality for jpg-compress (D1: fixed semantics).
_JPEG_COMPRESS_QUALITY = 60


def _open_image(source_path: Path) -> Image.Image:
    """Open an image with optional HEIC backend and decompression-bomb guard."""
    if source_path.suffix.lower() in {".heic", ".heif"}:
        try:
            import pillow_heif

            if hasattr(pillow_heif, "register_heif_opener"):
                pillow_heif.register_heif_opener()
        except ImportError as exc:  # pragma: no cover - requirements pin it
            raise RuntimeError(
                "pillow-heif is required to decode HEIC/HEIF input."
            ) from exc

    try:
        return Image.open(source_path)
    except Image.DecompressionBombError as exc:
        raise RuntimeError(
            "Image exceeds the maximum allowed pixel budget."
        ) from exc
    except (OSError, ValueError, SyntaxError) as exc:
        raise RuntimeError(f"Image input could not be decoded: {exc}") from exc


def _to_jpeg_safe_mode(image: Image.Image) -> Image.Image:
    """JPEG stores RGB / L / CMYK; anything else (RGBA, P, LA, ...) -> RGB."""
    if image.mode not in ("RGB", "L", "CMYK"):
        return image.convert("RGB")
    return image


def _shrink_guard(output_path: Path, source_path: Path) -> Path:
    """Never return a 'compressed' file larger than the input.

    Same guard as the certified pdf-compress plugin: when recompression
    does not shrink the file, the original bytes are returned instead.
    """
    try:
        if output_path.stat().st_size >= source_path.stat().st_size:
            output_path.write_bytes(source_path.read_bytes())
    except OSError:  # pragma: no cover - defensive
        pass
    return output_path


# ---------------------------------------------------------------------------
# Engine hooks (pure Pillow, one per slug, fixed semantics per D1)
# ---------------------------------------------------------------------------

def _convert_to_png(self, source_path, target_format, working_root):
    """Shared PNG re-encode hook (ICO decode is native; HEIC via pillow-heif)."""
    with _open_image(source_path) as image:
        image.load()
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")
        output_path = working_root / f"{source_path.stem}.{target_format}"
        image.save(output_path, format="PNG")
    return output_path


def _convert_jpg_rotate(self, source_path, target_format, working_root):
    """Rotate 90 degrees clockwise (fixed semantics, D1)."""
    with _open_image(source_path) as image:
        rotated = image.transpose(Image.Transpose.ROTATE_270)
        rotated = _to_jpeg_safe_mode(rotated)
        output_path = working_root / f"{source_path.stem}.{target_format}"
        rotated.save(output_path, format="JPEG", quality=95)
    return output_path


def _convert_jpg_flip(self, source_path, target_format, working_root):
    """Mirror horizontally (fixed semantics, D1)."""
    with _open_image(source_path) as image:
        flipped = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        flipped = _to_jpeg_safe_mode(flipped)
        output_path = working_root / f"{source_path.stem}.{target_format}"
        flipped.save(output_path, format="JPEG", quality=95)
    return output_path


def _convert_jpg_grayscale(self, source_path, target_format, working_root):
    """Convert to 8-bit grayscale (fixed semantics, D1)."""
    with _open_image(source_path) as image:
        gray = image.convert("L")
        output_path = working_root / f"{source_path.stem}.{target_format}"
        gray.save(output_path, format="JPEG", quality=95)
    return output_path


def _convert_jpg_compress(self, source_path, target_format, working_root):
    """Recompress JPEG at fixed quality 60 (fixed semantics, D1)."""
    with _open_image(source_path) as image:
        safe = _to_jpeg_safe_mode(image)
        output_path = working_root / f"{source_path.stem}.{target_format}"
        safe.save(output_path, format="JPEG", quality=_JPEG_COMPRESS_QUALITY)
    return _shrink_guard(output_path, source_path)


def _convert_png_compress(self, source_path, target_format, working_root):
    """Lossless PNG optimization (fixed semantics, D1)."""
    with _open_image(source_path) as image:
        output_path = working_root / f"{source_path.stem}.{target_format}"
        image.save(output_path, format="PNG", optimize=True)
    return _shrink_guard(output_path, source_path)


def _convert_jpg_crop(self, source_path, target_format, working_root):
    """Center crop to the middle 80% (fixed semantics, D1)."""
    with _open_image(source_path) as image:
        width, height = image.size
        inset_x, inset_y = int(width * 0.1), int(height * 0.1)
        box = (inset_x, inset_y, width - inset_x, height - inset_y)
        cropped = _to_jpeg_safe_mode(image.crop(box))
        output_path = working_root / f"{source_path.stem}.{target_format}"
        cropped.save(output_path, format="JPEG", quality=95)
    return output_path


def _convert_jpg_watermark(self, source_path, target_format, working_root):
    """Stamp the fixed CONVERIGO watermark bottom-right (D1 + D3)."""
    with _open_image(source_path) as image:
        base = image.convert("RGBA")
        font_size = max(12, min(base.width // 20, base.height // 4))
        try:
            font = ImageFont.load_default(size=font_size)
        except TypeError:  # pragma: no cover - Pillow < 10.1 fallback
            font = ImageFont.load_default()
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        left, top, right, bottom = draw.textbbox(
            (0, 0), _WATERMARK_TEXT, font=font
        )
        text_w, text_h = right - left, bottom - top
        margin = max(8, min(base.width, base.height) // 40)
        position = (
            max(0, base.width - text_w - margin),
            max(0, base.height - text_h - margin),
        )
        draw.text(position, _WATERMARK_TEXT, font=font, fill=(255, 255, 255, 140))
        watermarked = Image.alpha_composite(base, overlay).convert("RGB")
        output_path = working_root / f"{source_path.stem}.{target_format}"
        watermarked.save(output_path, format="JPEG", quality=95)
    return output_path


# ---------------------------------------------------------------------------
# Certified plugin definitions (D4: <format>-<operation> slugs)
# ---------------------------------------------------------------------------

IcoToPngPlugin = make_plugin_class(
    slug="ico-to-png",
    source_formats=["ico"],
    target_formats=["png"],
    engine_hook=_convert_to_png,
    name="ICO to PNG",
    description="Convert ICO icon files to PNG images.",
    category="image",
    engine="image",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="PNG Output",
    icon="🖼️",
    use_case="Best for turning favicons and desktop icons into editable PNG images.",
    seo_title="ICO to PNG Converter | Converigo",
    seo_description="Convert ICO icon files to PNG format quickly and easily.",
)

HeicToPngPlugin = make_plugin_class(
    slug="heic-to-png",
    source_formats=["heic"],
    target_formats=["png"],
    engine_hook=_convert_to_png,
    name="HEIC to PNG",
    description="Convert HEIC photos to PNG images with transparency support.",
    category="image",
    engine="image",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="PNG Output",
    icon="🖼️",
    use_case="Best for making Apple photos usable where PNG is required.",
    seo_title="HEIC to PNG Converter | Converigo",
    seo_description="Convert HEIC images to PNG format quickly and easily.",
)

JpgRotatePlugin = make_plugin_class(
    slug="jpg-rotate",
    source_formats=["jpg"],
    target_formats=["jpg"],
    engine_hook=_convert_jpg_rotate,
    name="JPG Rotate",
    description="Rotate JPG images 90 degrees clockwise.",
    category="image",
    engine="image",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="90° Clockwise",
    icon="🔄",
    use_case="Best for fixing sideways photos without installing an editor.",
    seo_title="JPG Rotate Tool | Converigo",
    seo_description="Rotate JPG images 90 degrees clockwise quickly and easily.",
)

JpgFlipPlugin = make_plugin_class(
    slug="jpg-flip",
    source_formats=["jpg"],
    target_formats=["jpg"],
    engine_hook=_convert_jpg_flip,
    name="JPG Flip",
    description="Flip JPG images horizontally (mirror).",
    category="image",
    engine="image",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="Mirrored",
    icon="↔️",
    use_case="Best for mirroring photos and scans in one click.",
    seo_title="JPG Flip Tool | Converigo",
    seo_description="Flip JPG images horizontally quickly and easily.",
)

JpgGrayscalePlugin = make_plugin_class(
    slug="jpg-grayscale",
    source_formats=["jpg"],
    target_formats=["jpg"],
    engine_hook=_convert_jpg_grayscale,
    name="JPG Grayscale",
    description="Convert JPG images to grayscale (black and white).",
    category="image",
    engine="image",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="B&W",
    icon="⚫",
    use_case="Best for print proofs and stylistic black-and-white photos.",
    seo_title="JPG Grayscale Tool | Converigo",
    seo_description="Convert JPG images to black and white quickly and easily.",
)

JpgCompressPlugin = make_plugin_class(
    slug="jpg-compress",
    source_formats=["jpg"],
    target_formats=["jpg"],
    engine_hook=_convert_jpg_compress,
    name="JPG Compress",
    description="Recompress JPG images at reduced quality to shrink file size.",
    category="image",
    engine="image",
    priority=75,
    quality=85,
    compatibility=95,
    estimated_saving=30,
    badge="Smaller Files",
    icon="🗜️",
    use_case="Best for shrinking JPG file size for sharing and uploads.",
    seo_title="JPG Compress Tool | Converigo",
    seo_description="Compress JPG images to reduce file size quickly and easily.",
)

PngCompressPlugin = make_plugin_class(
    slug="png-compress",
    source_formats=["png"],
    target_formats=["png"],
    engine_hook=_convert_png_compress,
    name="PNG Compress",
    description="Losslessly optimize PNG images to shrink file size.",
    category="image",
    engine="image",
    priority=75,
    quality=85,
    compatibility=95,
    estimated_saving=15,
    badge="Lossless",
    icon="🗜️",
    use_case="Best for shrinking PNG file size without losing any quality.",
    seo_title="PNG Compress Tool | Converigo",
    seo_description="Compress PNG images losslessly to reduce file size.",
)

JpgCropPlugin = make_plugin_class(
    slug="jpg-crop",
    source_formats=["jpg"],
    target_formats=["jpg"],
    engine_hook=_convert_jpg_crop,
    name="JPG Crop",
    description="Center-crop JPG images to the middle 80% area.",
    category="image",
    engine="image",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=10,
    badge="Center 80%",
    icon="✂️",
    use_case="Best for trimming photo edges to the central subject area.",
    seo_title="JPG Crop Tool | Converigo",
    seo_description="Center-crop JPG images quickly and easily.",
)

JpgWatermarkPlugin = make_plugin_class(
    slug="jpg-watermark",
    source_formats=["jpg"],
    target_formats=["jpg"],
    engine_hook=_convert_jpg_watermark,
    name="JPG Watermark",
    description="Stamp a semi-transparent CONVERIGO watermark on JPG images.",
    category="image",
    engine="image",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="Watermarked",
    icon="💧",
    use_case="Best for branding shared photos with a bottom-right stamp.",
    seo_title="JPG Watermark Tool | Converigo",
    seo_description="Add a watermark to JPG images quickly and easily.",
)