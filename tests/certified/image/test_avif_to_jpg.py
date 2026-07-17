from __future__ import annotations

# This certified test generates a small AVIF sample at runtime using the
# `pillow_avif` package when available. The test will skip if AVIF encoding
# support is not present in the running environment (keeps CI portable).
import pytest
from pathlib import Path

from PIL import Image

from app.engines.image_engine import ImageEngine


@pytest.mark.certified
@pytest.mark.asyncio
async def test_avif_to_jpg(tmp_path: Path) -> None:
    try:
        import pillow_avif
    except ImportError:
        pytest.skip("pillow_avif is not installed.")

    src = tmp_path / "sample.avif"
    # Create a tiny AVIF sample for the test; Pillow delegates to the
    # installed AVIF backend and will raise if encoding is unsupported.
    with Image.new("RGB", (200, 120), "white") as image:
        try:
            image.save(src, format="AVIF")
        except Exception as exc:
            pytest.skip(f"AVIF encoding support is not available in this environment: {exc}")

    assert src.exists(), "Failed to create AVIF sample for the test."

    engine = ImageEngine()
    out_path = await engine.convert(source_path=src, target_format="jpg")

    assert out_path.exists(), "Output jpg not created"
    assert out_path.suffix.lower() == ".jpg"
