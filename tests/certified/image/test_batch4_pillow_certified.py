"""Batch 4 certified tests — 10 Pillow-based image converter pairs.

Scope (user-approved Option B):
  bmp-to-png, bmp-to-webp, jpg-to-ico, jpg-to-tiff, png-to-bmp,
  png-to-ico, png-to-tiff, tiff-to-png, webp-to-ico, webp-to-tiff

Pattern follows tests/certified/image/test_jpg_to_webp_certified.py:
deterministic samples generated at runtime with Pillow, conversion executed
through the registered plugin, output validated for existence, extension,
and decodability.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.plugins.registry import registry

# (slug, source extension, target extension, sample mode)
BATCH4_PAIRS = [
    ("bmp-to-png", ".bmp", "png", "RGB"),
    ("bmp-to-webp", ".bmp", "webp", "RGB"),
    ("jpg-to-ico", ".jpg", "ico", "RGB"),
    ("jpg-to-tiff", ".jpg", "tiff", "RGB"),
    ("png-to-bmp", ".png", "bmp", "RGB"),
    ("png-to-ico", ".png", "ico", "RGBA"),
    ("png-to-tiff", ".png", "tiff", "RGB"),
    ("tiff-to-png", ".tiff", "png", "RGB"),
    ("webp-to-ico", ".webp", "ico", "RGB"),
    ("webp-to-tiff", ".webp", "tiff", "RGB"),
]

SAMPLE_TITLES = {
    ".bmp": "BMP",
    ".jpg": "JPG",
    ".png": "PNG",
    ".tiff": "TIFF",
    ".webp": "WEBP",
}


def _save_sample(path: Path, ext: str, mode: str) -> None:
    image = Image.new(mode, (64, 48))
    image.save(path)


def _mime(ext: str) -> str:
    return {
        ".bmp": "image/bmp",
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }[ext]


@pytest.mark.certified
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "slug,src_ext,target,mode",
    BATCH4_PAIRS,
    ids=[p[0] for p in BATCH4_PAIRS],
)
async def test_batch4_pair_certified(
    tmp_path: Path, slug: str, src_ext: str, target: str, mode: str
) -> None:
    # 1) Plugin must be registered, routed to the image engine, and resolvable
    #    by slug for the declared pair (same resolution as the /convert router).
    src_fmt = src_ext.lstrip(".")
    plugin = registry.get_plugin(src_fmt, target, slug)
    assert plugin is not None, f"Plugin '{slug}' not registered."
    assert plugin.engine == "image", f"'{slug}' must use the image engine."

    # 2) Plugin declares the pair.
    assert src_fmt in plugin.source_formats
    assert target in plugin.target_formats

    # 3) Deterministic real sample.
    src = tmp_path / f"sample{src_ext}"
    _save_sample(src, src_ext, mode)
    assert src.exists() and src.stat().st_size > 0

    # 4) Convert through the plugin.
    out_path = await plugin.convert(
        source_path=src,
        target_format=target,
        output_dir=tmp_path,
        temp_dir=tmp_path,
    )

    # 5) Output validation.
    assert out_path.exists(), f"'{slug}': output not created."
    assert out_path.suffix.lower() == f".{target}", (
        f"'{slug}': unexpected output extension {out_path.suffix}"
    )
    assert out_path.stat().st_size > 0, f"'{slug}': output is empty."

    with Image.open(out_path) as result:
        result.verify()  # raises if the file is not a decodable image

    with Image.open(out_path) as result2:
        assert result2.size[0] > 0 and result2.size[1] > 0


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,src_ext,target,mode",
    BATCH4_PAIRS,
    ids=[p[0] for p in BATCH4_PAIRS],
)
def test_batch4_pair_contract_files(slug: str, src_ext: str, target: str, mode: str) -> None:
    """Contract JSON must exist and declare the certified pair correctly."""
    import json

    contract_path = (
        Path(__file__).resolve().parents[3]
        / "app" / "data" / "converters" / f"{slug}.contract.json"
    )
    assert contract_path.exists(), f"Missing contract file for '{slug}'."
    with open(contract_path, encoding="utf-8") as fh:
        contract = json.load(fh)

    assert contract["slug"] == slug
    assert contract["conversion_engine"] == "image"
    assert contract["lifecycle_status"] == "certified"
    assert src_ext.lstrip(".") in contract["input_formats"]
    assert target in contract["output_formats"]
    assert _mime(src_ext) in contract["accepted_mime_types"]
