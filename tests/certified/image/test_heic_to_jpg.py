from __future__ import annotations

# This certified test generates a small HEIF/HEIC sample at runtime using
# the installed `pillow_heif` package (it registers a HEIF opener). Tests
# skip when `pillow_heif` or HEIF support is not available in the environment
# to keep CI stable across platforms.
import pytest
from pathlib import Path

from PIL import Image

from app.engines.image_engine import ImageEngine


@pytest.mark.certified
@pytest.mark.asyncio
async def test_heic_to_jpg(tmp_path: Path) -> None:
    try:
        import pillow_heif
    except ImportError:
        pytest.skip("pillow_heif is not installed.")

    if not hasattr(pillow_heif, "register_heif_opener"):
        pytest.skip("Installed pillow_heif package does not support HEIF opener registration.")

    # Register opener (enables Pillow to handle HEIF/HEIC files)
    pillow_heif.register_heif_opener()

    src = tmp_path / "sample.heic"
    with Image.new("RGB", (200, 120), "white") as image:
        image.save(src, format="HEIF")

    assert src.exists(), "Failed to create HEIC sample for the test."

    engine = ImageEngine()
    out_path = await engine.convert(source_path=src, target_format="jpg")

    assert out_path.exists(), "Output jpg not created"
    assert out_path.suffix.lower() == ".jpg"

