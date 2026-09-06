"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F8)
Version : 1.0.0

Base64 <-> Image data-transport converters (F8-A: image-to-base64,
base64-to-image).  Built on the F0 certified factory scaffolding: the
conversion pipeline (discovery -> supports() check -> working root ->
single servable file -> non-empty output -> honest error) is owned by
FactoryConversionPlugin.

Supervisor-approved MVP semantics (F8 audit):
- image-to-base64: BIT-EXACT transport.  The ORIGINAL uploaded bytes are
  embedded verbatim (no PIL re-encode) into ONE .txt file whose entire
  content is a single RFC 2397 data URI:
      data:image/<mime>;base64,<payload>
  so our own base64-to-image can round-trip it.  Sources: the static
  raster whitelist (jpg/jpeg/png/webp/bmp/gif/tiff).
- base64-to-image: input via the txt channel (txt is already whitelisted
  with FILE_SIGNATURES "[]" per the audit).  The file must contain
  exactly ONE data URI (data:image/*;base64,...).  The payload is
  decoded (validate=True), size-capped, verified through PIL, and
  re-encoded to the requested raster target (deterministic single-file
  output; re-encode disclosed on the landing page).
- Mandatory size cap (audit: "cap ukuran wajib"): text payload over
  _MAX_PAYLOAD_BYTES (20 MiB decoded) -> honest 422.
"""
from __future__ import annotations

import base64 as _base64
import binascii as _binascii
import re
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.factory import make_plugin_class

#: Mandatory decoded-payload ceiling (audit requirement: size-capped decode).
_MAX_PAYLOAD_BYTES = 20 * 1024 * 1024

#: Source extension -> RFC 2397 MIME type (bit-exact transport, no guessing).
_MIME_BY_SOURCE = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "gif": "image/gif",
    "tiff": "image/tiff",
}

#: Data-URI MIME -> canonical extension (for honest mismatch errors).
_EXT_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/gif": "gif",
    "image/tiff": "tiff",
}

#: Exactly one data URI, payload base64 alphabet (+ tolerated whitespace).
_DATA_URI_RE = re.compile(
    r"^data:(image/[A-Za-z0-9.+-]+);base64,([A-Za-z0-9+/=\s]+?)\s*$",
    re.DOTALL,
)


def _unsupported(source: str, target: str, message: str) -> Exception:
    """Lazily build the honest-422 error (rar-extract/F4 lazy-import precedent)."""
    from app.services.conversion_service import UnsupportedConversionError

    return UnsupportedConversionError(source, target, message)


def _convert_image_to_base64(
    plugin: object, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Embed the ORIGINAL bytes verbatim in a single data URI .txt file."""
    source = source_path.suffix.lower().lstrip(".")
    mime = _MIME_BY_SOURCE.get(source)
    if mime is None:  # pragma: no cover - supports() already gates this
        raise _unsupported(
            "image", "txt", "Image to base64 conversion failed: unsupported image type."
        )

    payload = source_path.read_bytes()
    encoded = _base64.b64encode(payload).decode("ascii")
    output_path = working_root / f"{source_path.stem}.txt"
    output_path.write_text(f"data:{mime};base64,{encoded}\n", encoding="ascii")
    return output_path


def _convert_base64_to_image(
    plugin: object, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Decode ONE data URI from the txt input, verify through PIL, and
    re-encode to the requested raster target (deterministic output)."""
    target = target_format.lower().lstrip(".")
    raw = source_path.read_text(encoding="utf-8", errors="strict")
    match = _DATA_URI_RE.match(raw.strip())
    if not match:
        raise _unsupported(
            "txt",
            "image",
            "Base64 to image conversion failed: the file must contain exactly "
            "one data URI of the form data:image/<type>;base64,<payload>.",
        )

    mime = match.group(1).lower()
    declared_ext = _EXT_BY_MIME.get(mime)
    if declared_ext is None:
        raise _unsupported(
            "txt",
            "image",
            "Base64 to image conversion failed: unsupported data URI image "
            f"type '{mime}'.",
        )

    compact = re.sub(r"\s+", "", match.group(2))
    try:
        payload = _base64.b64decode(compact, validate=True)
    except (_binascii.Error, ValueError) as exc:
        raise _unsupported(
            "txt",
            "image",
            f"Base64 to image conversion failed: payload is not valid base64 ({exc}).",
        ) from exc

    if len(payload) > _MAX_PAYLOAD_BYTES:
        raise _unsupported(
            "txt",
            "image",
            "Base64 to image conversion failed: decoded payload exceeds the "
            f"maximum of {_MAX_PAYLOAD_BYTES} bytes.",
        )

    try:
        with Image.open(BytesIO(payload)) as image:
            image.load()
    except Image.DecompressionBombError as exc:
        raise RuntimeError("Image exceeds the maximum allowed pixel budget.") from exc
    except (OSError, ValueError, SyntaxError) as exc:
        raise _unsupported(
            "txt",
            "image",
            "Base64 to image conversion failed: the decoded payload is not a "
            f"readable {declared_ext.upper()} image ({exc}).",
        ) from exc

    save_format = "JPEG" if target in {"jpg", "jpeg"} else target.upper()
    output_path = working_root / f"{source_path.stem}.{target}"
    try:
        image.save(output_path, format=save_format)
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"Base64 to image conversion failed: could not re-encode to "
            f"{save_format} ({exc})."
        ) from exc
    return output_path


ImageToBase64Plugin = make_plugin_class(
    slug="image-to-base64",
    source_formats=["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"],
    target_formats=["txt"],
    engine_hook=_convert_image_to_base64,
    name="Image to Base64",
    description="Encode JPG, PNG, WebP, BMP, GIF, or TIFF images as a single Base64 data URI text file.",
    category="image",
    engine="image",
    goal="conversion",
    use_case="Best for embedding images directly into HTML, CSS, JSON, or Markdown payloads.",
    priority=60,
    quality=90,
    compatibility=95,
    estimated_saving=0,
    badge="Data URI",
    icon="🔡",
    seo_title="Image to Base64 Converter | Converigo",
    seo_description="Encode images as Base64 data URIs quickly and easily.",
    working_subdir="data",
)

Base64ToImagePlugin = make_plugin_class(
    slug="base64-to-image",
    source_formats=["txt"],
    target_formats=["png", "jpg", "webp", "bmp", "gif", "tiff"],
    engine_hook=_convert_base64_to_image,
    name="Base64 to Image",
    description="Decode a Base64 data URI text file back into a real image file.",
    category="image",
    engine="image",
    goal="conversion",
    use_case="Best for turning copied data URIs back into downloadable image files.",
    priority=60,
    quality=90,
    compatibility=95,
    estimated_saving=0,
    badge="Data URI",
    icon="🖼️",
    seo_title="Base64 to Image Converter | Converigo",
    seo_description="Decode Base64 data URIs back into PNG, JPG, or WebP images quickly and easily.",
    working_subdir="data",
)
