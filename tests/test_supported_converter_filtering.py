import json
from pathlib import Path

from app.services.converter_data_service import ConverterDataService


def _write_converter(path: Path, slug: str, **kwargs) -> None:
    payload = {
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "description": f"{slug} converter",
        "source": kwargs.get("source", "src"),
        "target": kwargs.get("target", "dst"),
        "active": kwargs.get("active", True),
    }
    payload.update(kwargs)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_supported_converters_filter_out_unbacked_active_converters(tmp_path: Path) -> None:
    # Create one supported converter and one active converter with no plugin support.
    _write_converter(
        tmp_path / "jpg-to-png.json",
        slug="jpg-to-png",
        source="jpg",
        target="png",
    )
    _write_converter(
        tmp_path / "magic-to-pdf.json",
        slug="magic-to-pdf",
        source="magic",
        target="pdf",
    )

    service = ConverterDataService(tmp_path)

    all_active_slugs = {converter["slug"] for converter in service.list_active_converters()}
    supported_slugs = {converter["slug"] for converter in service.list_supported_converters()}

    assert "jpg-to-png" in all_active_slugs
    assert "magic-to-pdf" in all_active_slugs
    assert "jpg-to-png" in supported_slugs
    assert "magic-to-pdf" not in supported_slugs


def test_homepage_only_shows_supported_converters(tmp_path: Path) -> None:
    _write_converter(
        tmp_path / "png-to-jpg.json",
        slug="png-to-jpg",
        source="png",
        target="jpg",
        popular=True,
    )
    _write_converter(
        tmp_path / "fake-to-pdf.json",
        slug="fake-to-pdf",
        source="fake",
        target="pdf",
        popular=True,
    )

    service = ConverterDataService(tmp_path)
    home_slugs = {converter["slug"] for converter in service.list_popular_converters(limit=10)}

    assert "png-to-jpg" in home_slugs
    assert "fake-to-pdf" not in home_slugs


def test_public_converters_exclude_unsupported_converters(tmp_path: Path) -> None:
    _write_converter(
        tmp_path / "png-to-jpg.json",
        slug="png-to-jpg",
        source="png",
        target="jpg",
        public=True,
    )
    _write_converter(
        tmp_path / "ghost-to-pdf.json",
        slug="ghost-to-pdf",
        source="ghost",
        target="pdf",
        public=True,
    )

    service = ConverterDataService(tmp_path)
    public_slugs = {converter["slug"] for converter in service.list_public_converters()}

    assert "png-to-jpg" in public_slugs
    assert "ghost-to-pdf" not in public_slugs
