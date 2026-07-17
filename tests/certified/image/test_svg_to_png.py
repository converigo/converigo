from __future__ import annotations

# This certified SVG test uses CairoSVG to render a minimal inline SVG when
# no repository sample is available. It skips cleanly if CairoSVG or native
# Cairo libraries are not present on the host, avoiding hard failures.
import pytest
from pathlib import Path

from app.engines.image_engine import ImageEngine


@pytest.mark.certified
@pytest.mark.asyncio
async def test_svg_to_png(tmp_path: Path) -> None:
    try:
        import cairosvg
    except (ImportError, OSError) as exc:
        pytest.skip(f"SVG conversion dependencies are unavailable: {exc}")

    src = Path("test_files") / "sample.svg"
    if not src.exists():
        src = tmp_path / "sample.svg"
        src.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
            '<rect width="200" height="120" fill="white"/>'
            '<text x="20" y="65" font-size="20" fill="black">Test</text>'
            '</svg>',
            encoding="utf-8",
        )

    engine = ImageEngine()
    out_path = await engine.convert(source_path=src, target_format="png")

    assert out_path.exists(), "Output png not created"
    assert out_path.suffix.lower() == ".png"
