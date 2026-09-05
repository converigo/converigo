"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F2)
Version : 1.0.0

In-image probe for Factory Batch F2 (cluster G-B: Image Operations).

Executed INSIDE the production image by docker-runtime-verify step [4/5]:

    python scripts/ci_in_image_image_ops_probe.py

All fixtures are generated in-image with Pillow / pillow-heif (both are
requirements of the production image), so the probe is self-sufficient
exactly like the F1 TSV probe.  Each of the nine F2 factory plugins is
resolved through the real registry, executed against a temp working
dir, and the output is re-opened and validated (format + dimensions +
content checks).  Exit code 0 = PASS.
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from app.plugins.registry import registry  # noqa: E402


def _make_fixtures(root: Path) -> dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    jpg = root / "probe.jpg"
    Image.new("RGB", (64, 40), (30, 144, 255)).save(jpg, format="JPEG", quality=95)

    png = root / "probe.png"
    Image.new("RGBA", (64, 40), (34, 139, 34, 255)).save(png, format="PNG")

    ico = root / "probe.ico"
    Image.new("RGBA", (32, 32), (255, 140, 0, 255)).save(
        ico, format="ICO", sizes=[(32, 32)]
    )

    import pillow_heif

    pillow_heif.register_heif_opener()
    heic = root / "probe.heic"
    Image.new("RGB", (48, 32), (128, 0, 128)).save(heic, format="HEIF")

    return {"jpg": jpg, "png": png, "ico": ico, "heic": heic}


def _run(slug: str, fixture: Path, target_format: str, check) -> None:
    assert registry.has_slug(slug), f"{slug} not registered"
    plugin = registry.by_slug[slug]
    output = asyncio.run(plugin.convert(fixture, target_format))
    assert output.is_file(), f"{slug}: no output file {output}"
    check(output)
    print(f"PROBE {slug}: {fixture.name} -> {output.name} OK")


def _png_ok(path: Path) -> None:
    image = Image.open(path)
    assert image.format == "PNG", image.format
    image.load()


def _jpg_ok(path: Path) -> None:
    image = Image.open(path)
    assert image.format == "JPEG", image.format
    image.load()


def _rotate_check(path: Path) -> None:
    image = Image.open(path)
    assert (
        image.format == "JPEG" and image.height > image.width
    ), (image.format, image.size)
    image.load()


def _size_check(expected: tuple[int, int]):
    def _check(path: Path) -> None:
        image = Image.open(path)
        assert image.size == expected, image.size
        image.load()

    return _check


def _heic_to_png_check(path: Path) -> None:
    image = Image.open(path)
    assert image.format == "PNG" and image.size == (48, 32), (
        image.format,
        image.size,
    )
    image.load()


def _png_shrink_check(source: Path):
    def _check(path: Path) -> None:
        _png_ok(path)
        assert path.stat().st_size <= source.stat().st_size

    return _check


def _watermark_check(path: Path) -> None:
    image = Image.open(path)
    assert image.format == "JPEG" and image.size == (200, 100), (
        image.format,
        image.size,
    )
    # A bright (white-ish) stamped pixel must exist in the bottom-right
    # region; the far corner keeps the solid source colour.
    bright = any(
        sum(image.getpixel((x, y))[:3]) > 500
        for x in range(120, 199, 2)
        for y in range(70, 99, 2)
    )
    assert bright, "no watermark pixel found in bottom-right region"
    image.load()


def main(_argv: list[str]) -> int:
    with tempfile.TemporaryDirectory(prefix="f2_probe_") as tmp:
        fixtures = _make_fixtures(Path(tmp))
        jpg, png = fixtures["jpg"], fixtures["png"]
        _run("ico-to-png", fixtures["ico"], "png", _png_ok)
        _run("heic-to-png", fixtures["heic"], "png", _heic_to_png_check)
        _run("jpg-rotate", jpg, "jpg", _rotate_check)
        _run("jpg-flip", jpg, "jpg", _size_check((64, 40)))
        _run("jpg-grayscale", jpg, "jpg", _size_check((64, 40)))
        _run("jpg-compress", jpg, "jpg", _jpg_ok)
        _run("png-compress", png, "png", _png_shrink_check(png))
        _run("jpg-crop", jpg, "jpg", _size_check((52, 32)))
        watermark = Path(tmp) / "probe_wm.jpg"
        Image.new("RGB", (200, 100), (30, 144, 255)).save(
            watermark, format="JPEG", quality=95
        )
        _run("jpg-watermark", watermark, "jpg", _watermark_check)
    print("F2 IN-IMAGE PROBE PASS: 9 image ops converters OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))