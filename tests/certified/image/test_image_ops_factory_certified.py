"""
PROJECT: CONVERIGO
TEST SUITE: Certified Image Ops Cluster - Factory Batch F2 (Jalur 2)

Factory Batch Plan F2 (cluster G-B net-new): nine image-operation
converters built on the F0 factory base (app/factory/plugin_base.py):

    ico-to-png, heic-to-png, jpg-rotate, jpg-flip, jpg-grayscale,
    jpg-compress, png-compress, jpg-crop, jpg-watermark

ONE parametric test file for the whole F2 batch, using the shared
factory harness uniform contract:

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    output content verified -> honest 422 UNSUPPORTED_CONVERSION

Governance note: IMG-37 jpg-to-tiff and IMG-36 png-to-tiff from the
original G-B candidate list were already installed and certified before
F2; Base64 <-> Image (VAR-39/40) was deferred by the Supervisor (D2).
Fixtures are generated in-memory with Pillow/pillow-heif (both already
required by the image engine), so the suite adds zero binary assets
except the tiny tracked tests/sample.ico regression sample.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from tests.certified._factory_harness import (
    assert_honest_unsupported,
    assert_slug_discovered,
    cleanup_output,
    post_convert,
    run_happy_path,
)


# ---------------------------------------------------------------------------
# Fixture builders (real images, deterministic content)
# ---------------------------------------------------------------------------

def _make_jpg(path: Path, width: int = 64, height: int = 40) -> Path:
    image = Image.new("RGB", (width, height), (30, 144, 255))
    image.save(path, format="JPEG", quality=95)
    return path


def _make_two_tone_jpg(path: Path) -> Path:
    """Left half red, right half blue: makes the horizontal flip observable."""
    image = Image.new("RGB", (64, 40), (220, 30, 30))
    for x in range(32, 64):
        for y in range(40):
            image.putpixel((x, y), (30, 30, 220))
    image.save(path, format="JPEG", quality=95)
    return path


def _make_watermark_jpg(path: Path) -> Path:
    return _make_jpg(path, width=200, height=100)


def _make_png(path: Path, width: int = 64, height: int = 40) -> Path:
    image = Image.new("RGBA", (width, height), (34, 139, 34, 255))
    image.save(path, format="PNG")
    return path


def _make_ico(path: Path) -> Path:
    image = Image.new("RGBA", (32, 32), (255, 140, 0, 255))
    image.save(path, format="ICO", sizes=[(32, 32)])
    return path


def _make_heic(path: Path) -> Path:
    import pillow_heif

    pillow_heif.register_heif_opener()
    image = Image.new("RGB", (48, 32), (128, 0, 128))
    image.save(path, format="HEIF")
    return path


# ---------------------------------------------------------------------------
# Content verifiers per operation (fixed semantics per Supervisor D1)
# ---------------------------------------------------------------------------

def _load(path: Path) -> Image.Image:
    return Image.open(path)


def _verify_png_out(path: Path) -> None:
    image = Image.open(path)
    assert image.format == "PNG", image.format
    image.load()


def _verify_rotate(path: Path) -> None:
    image = _load(path)
    assert image.format == "JPEG"
    # 90 CW: a wide image becomes tall.
    assert image.height > image.width, image.size


def _verify_flip(path: Path) -> None:
    image = _load(path)
    assert image.format == "JPEG"
    assert image.size == (64, 40), image.size
    # Two-tone source: after a horizontal mirror the right half must be red.
    assert image.getpixel((60, 20))[0] > image.getpixel((60, 20))[2], (
        image.getpixel((60, 20))
    )


def _verify_grayscale(path: Path) -> None:
    image = _load(path)
    assert image.format == "JPEG"
    assert image.mode in ("L", "RGB")
    if image.mode == "RGB":
        extrema = [image.getchannel(c).getextrema() for c in ("R", "G", "B")]
        lows = [lo for lo, _ in extrema]
        highs = [hi for _, hi in extrema]
        assert max(highs) - min(highs) <= 1 and max(lows) - min(lows) <= 1, extrema


def _verify_jpg_compress(path: Path) -> None:
    image = _load(path)
    assert image.format == "JPEG"
    assert path.stat().st_size > 0


def _verify_png_compress(path: Path) -> None:
    image = _load(path)
    assert image.format == "PNG"
    assert image.size == (64, 40), image.size


def _verify_crop(path: Path) -> None:
    image = _load(path)
    assert image.format == "JPEG"
    assert image.size == (52, 32), image.size  # center 80% of 64x40


def _verify_watermark(path: Path) -> None:
    image = _load(path)
    assert image.format == "JPEG"
    assert image.size == (200, 100), image.size
    # A bright (white-ish) stamped pixel must exist in the bottom-right
    # region; the far corner keeps the solid source colour (30, 144, 255).
    assert image.getpixel((2, 2)) == (30, 144, 255)
    bright = any(
        sum(image.getpixel((x, y))[:3]) > 500
        for x in range(120, 199, 2)
        for y in range(70, 99, 2)
    )
    assert bright, "no watermark pixel found in bottom-right region"


# ---------------------------------------------------------------------------
# Case table: (slug, target_format, fixture_builder, mime, verifier)
# ---------------------------------------------------------------------------

CASES = [
    ("ico-to-png", "png", _make_ico, "image/x-icon", _verify_png_out),
    ("heic-to-png", "png", _make_heic, "image/heic", _verify_png_out),
    ("jpg-rotate", "jpg", _make_jpg, "image/jpeg", _verify_rotate),
    ("jpg-flip", "jpg", _make_two_tone_jpg, "image/jpeg", _verify_flip),
    ("jpg-grayscale", "jpg", _make_jpg, "image/jpeg", _verify_grayscale),
    ("jpg-compress", "jpg", _make_jpg, "image/jpeg", _verify_jpg_compress),
    ("png-compress", "png", _make_png, "image/png", _verify_png_compress),
    ("jpg-crop", "jpg", _make_jpg, "image/jpeg", _verify_crop),
    ("jpg-watermark", "jpg", _make_watermark_jpg, "image/jpeg", _verify_watermark),
]


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,expected_source",
    [
        (slug, target, slug.split("-")[0])
        for slug, target, _, _, _ in CASES
    ],
)
def test_factory_plugin_discovered(slug: str, target_format: str, expected_source: str) -> None:
    """Each F2 slug is registered with its (source, target) pair."""
    assert_slug_discovered(slug, expected_source, target_format)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,builder,mime,verifier",
    [
        pytest.param(slug, target, builder, mime, verifier, id=slug)
        for slug, target, builder, mime, verifier in CASES
    ],
)
def test_factory_happy_path_uniform_contract(
    slug: str,
    target_format: str,
    builder,
    mime: str,
    verifier,
    tmp_path: Path,
) -> None:
    """Uniform pipeline: 201 -> download 200 -> content verified per case."""
    fixture = builder(tmp_path / f"factory_fixture.{slug.split('-')[0]}")
    assert fixture.is_file(), f"fixture builder produced no file: {fixture}"
    output = run_happy_path(fixture, target_format, slug, mime=mime)
    try:
        verifier(output)
    finally:
        cleanup_output(output)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format",
    [(slug, target) for slug, target, _, _, _ in CASES],
)
def test_factory_honest_error_for_unsupported_input(
    slug: str,
    target_format: str,
) -> None:
    """Wrong-extension input gets the honest 422 error class - never fake output."""
    response = post_convert(
        Path("tests/sample.txt"),
        target_format,
        slug,
        mime="text/plain",
        filename="sample.txt",
    )
    assert_honest_unsupported(response)


# ---------------------------------------------------------------------------
# F2-specific: self-pair slug resolution (Supervisor D4 / F2 audit caveat)
# ---------------------------------------------------------------------------

SELF_PAIR_OPS = [
    "jpg-rotate",
    "jpg-flip",
    "jpg-grayscale",
    "jpg-compress",
    "jpg-crop",
    "jpg-watermark",
]


@pytest.mark.certified
def test_self_pair_operations_resolve_to_distinct_plugins() -> None:
    """Every (jpg, jpg) operation is reachable via its own slug and the six
    operations never overwrite each other at the slug level (the same
    slug-aware pattern as the pdf-compress / pdf-split precedent)."""
    from app.plugins.registry import registry

    resolved = []
    for slug in SELF_PAIR_OPS:
        assert registry.has_slug(slug), slug
        plugin = registry.get_plugin("jpg", "jpg", slug=slug)
        assert plugin.slug == slug
        resolved.append(type(plugin).__name__)

    assert len(set(resolved)) == len(SELF_PAIR_OPS), resolved


@pytest.mark.certified
def test_self_pair_legacy_pair_index_still_resolves() -> None:
    """The shared (jpg, jpg) legacy pair index still holds exactly one
    deterministic plugin (last-registered wins, like (pdf, pdf))."""
    from app.plugins.registry import registry

    legacy = registry.get_plugin("jpg", "jpg")
    assert legacy is not None
    assert registry.get_plugin("jpg", "jpg") is legacy


@pytest.mark.certified
def test_operation_slugs_never_leak_into_dropdown_map() -> None:
    """Self-pairs are excluded from the registry-derived target map, so the
    F2 operations do not change the converter dropdown (ico/heic gains are
    format converters and ARE expected)."""
    from app.plugins.registry import registry

    jpg_targets = {
        tgt
        for (src, tgt) in registry.plugins
        if src == "jpg" and tgt != "jpg" and tgt != "jpeg"
    }
    assert jpg_targets == {"ico", "pdf", "png", "tiff", "webp"}
    assert ("jpg", "jpg") in registry.plugins  # ops live here, off the map
    assert ("ico", "png") in registry.plugins
    assert ("heic", "png") in registry.plugins