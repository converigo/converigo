from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import pytest

from app.core.registry import ConverterInfo, ConverterRegistry
from app.services.sitemap_service import SitemapService


def test_sitemap_service_generates_category_sitemaps_and_validates_entries(tmp_path: Path) -> None:
    registry = ConverterRegistry()
    registry.register(
        ConverterInfo(
            id="mp4_to_webm",
            name="MP4 to WebM",
            category="video",
            source_format="mp4",
            target_format="webm",
            enabled=True,
        )
    )
    registry.register(
        ConverterInfo(
            id="png_to_jpg",
            name="PNG to JPG",
            category="image",
            source_format="png",
            target_format="jpg",
            enabled=True,
        )
    )
    registry.register(
        ConverterInfo(
            id="pdf_to_jpg",
            name="PDF to JPG",
            category="pdf",
            source_format="pdf",
            target_format="jpg",
            enabled=True,
        )
    )
    registry.register(
        ConverterInfo(
            id="mp3_to_wav",
            name="MP3 to WAV",
            category="audio",
            source_format="mp3",
            target_format="wav",
            enabled=True,
        )
    )

    service = SitemapService(output_dir=tmp_path, registry_instance=registry)
    generated_files = service.generate_all(base_url="https://converigo.com")

    expected_files = {
        "sitemap.xml",
        "sitemap-video.xml",
        "sitemap-image.xml",
        "sitemap-pdf.xml",
        "sitemap-audio.xml",
    }
    assert expected_files.issubset(set(generated_files))

    issues = service.validate()
    assert issues == []

    urls: list[str] = []
    for filename in ["sitemap-video.xml", "sitemap-image.xml", "sitemap-pdf.xml", "sitemap-audio.xml"]:
        root = ET.parse(tmp_path / filename).getroot()
        namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls.extend(loc.text for loc in root.findall(".//sm:url/sm:loc", namespaces))

    assert urls.count("https://converigo.com/mp4-to-webm") == 1
    assert urls.count("https://converigo.com/png-to-jpg") == 1
    assert urls.count("https://converigo.com/pdf-to-jpg") == 1
    assert urls.count("https://converigo.com/mp3-to-wav") == 1


def test_sitemap_service_rejects_duplicate_urls_and_orphan_landing_pages(tmp_path: Path) -> None:
    registry = ConverterRegistry()
    registry.register(
        SimpleNamespace(
            id="dup_a",
            name="Duplicate A",
            category="image",
            source_format="png",
            target_format="jpg",
            landing_path="/image/dup",
            canonical_url="https://converigo.com/image/dup",
            enabled=True,
        )
    )
    registry.register(
        SimpleNamespace(
            id="dup_b",
            name="Duplicate B",
            category="image",
            source_format="png",
            target_format="jpg",
            landing_path="/image/dup",
            canonical_url="https://converigo.com/image/dup",
            enabled=True,
        )
    )
    registry.register(
        SimpleNamespace(
            id="missing_landing",
            name="Missing Landing",
            category="audio",
            source_format="mp3",
            target_format="wav",
            canonical_url="https://converigo.com/audio/missing-landing",
            enabled=True,
        )
    )

    service = SitemapService(output_dir=tmp_path, registry_instance=registry)

    with pytest.raises(ValueError, match="Duplicate URL"):
        service.generate_all(base_url="https://converigo.com")
