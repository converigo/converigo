from pathlib import Path

from xml.etree import ElementTree as ET

from fastapi.testclient import TestClient

from app.main import app
from app.services.converter_data_service import ConverterDataService


def test_sitemap_contains_homepage_converter_and_trust_pages():
    client = TestClient(app)
    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")

    root = ET.fromstring(response.text)
    namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [loc.text for loc in root.findall(".//sm:url/sm:loc", namespaces)]

    assert any(loc.endswith("/") for loc in locations)
    assert any("/tools/" in loc for loc in locations)
    assert any(loc.endswith("/about") for loc in locations)
    assert any(loc.endswith("/privacy-policy") for loc in locations)
    assert any(loc.endswith("/terms") for loc in locations)
    assert any(loc.endswith("/contact") for loc in locations)
    assert any(loc.endswith("/cookies") for loc in locations)
    assert any(loc.endswith("/tools/mp4-to-mp3") for loc in locations)
    assert any(loc.endswith("/tools/jpg-to-pdf") for loc in locations)
    assert any(loc.endswith("/tools/png-to-jpg") for loc in locations)
    assert any(loc.endswith("/tools/pdf-to-jpg") for loc in locations)
    assert any(loc.endswith("/blog") for loc in locations)
    # Cross-cluster duplicate (GSC INDEX RECOVERY, root cause #2): the legacy
    # /blog/how-to-convert-mp4-to-mp3 article is intentionally excluded from the
    # sitemap; it now canonicalizes to the Learning Center primary at
    # /learning/how-to-convert-mp4-to-mp3 (asserted below), which stays listed.
    assert not any(loc.endswith("/blog/how-to-convert-mp4-to-mp3") for loc in locations)
    assert any(loc.endswith("/blog/jpg-to-pdf-guide") for loc in locations)
    assert any(loc.endswith("/blog/png-to-jpg-guide") for loc in locations)
    assert any(loc.endswith("/learning") for loc in locations)
    assert any(loc.endswith("/learning/what-is-file-conversion") for loc in locations)
    assert any(loc.endswith("/learning/how-to-convert-mp4-to-mp3") for loc in locations)
    assert not any(loc.endswith("/mp4-to-mp3") and "/tools/" not in loc for loc in locations)
    assert not any(loc.endswith("/jpg-to-pdf") and "/tools/" not in loc for loc in locations)
    assert not any(loc.endswith("/png-to-jpg") and "/tools/" not in loc for loc in locations)
    assert not any(loc.endswith("/pdf-to-jpg") and "/tools/" not in loc for loc in locations)


# G14 alias dedupe data dir (tests run from the repo root, same convention as
# tests/test_f2_noindex_policy.py).
CONVERTERS_DIR = Path("app/data/converters")


def _sitemap_locations():
    client = TestClient(app)
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    root = ET.fromstring(response.text)
    namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text for loc in root.findall(".//sm:url/sm:loc", namespaces)]


def _published_pairs(service):
    pairs = {}
    for tool in service.list_supported_converters():
        slug = str(tool.get("slug", "")).strip().lower()
        pairs[slug] = (
            str(tool.get("source", "")).strip().lower(),
            str(tool.get("target", "")).strip().lower(),
        )
    return pairs


def test_sitemap_suppresses_only_the_pptx_to_jpg_alias():
    """Pair-level alias dedupe (GSC INDEX RECOVERY, root cause #3).

    pptx-to-jpg is a dynamically generated plugin (abc.PptxToJpgPlugin) that
    claims the ('pptx', 'jpg') pair, competing with the real PPTToJPGPlugin
    published as ppt-to-jpg. Both are plugin-backed and both are published for
    the same non-self pair, so both /tools pages were submitted to crawlers as
    duplicate content. The sitemap must now submit only the converter the
    plugin registry actually dispatches for the pair (ppt-to-jpg), while every
    legitimate same-pair tool stays published.
    """
    locations = _sitemap_locations()
    pairs = _published_pairs(ConverterDataService(CONVERTERS_DIR))

    # The shadowed alias must be gone, the canonical converter retained.
    assert any(loc.endswith("/tools/ppt-to-jpg") for loc in locations)
    assert not any(loc.endswith("/tools/pptx-to-jpg") for loc in locations)

    # Exactly one published URL per genuine duplicate pair: every published
    # converter still declaring ('pptx', 'jpg') maps to a single sitemap loc.
    published_pptx_jpg = [
        slug for slug, pair in pairs.items() if pair == ("pptx", "jpg")
    ]
    assert published_pptx_jpg, "pptx->jpg converters disappeared from the catalog"
    emitted = {
        loc.rsplit("/tools/", 1)[-1]
        for loc in locations
        if "/tools/" in loc
    }
    assert [slug for slug in published_pptx_jpg if slug in emitted] == [
        "ppt-to-jpg"
    ]

    # Carve-outs: legitimate same-pair tools must remain published. If one of
    # these is ever de-indexed, the dedupe regressed to a naive pair filter.
    for slug, rationale in (
        ("jpg-crop", "self-pair operation (jpg, jpg)"),
        ("pdf-merge", "self-pair operation (pdf, pdf)"),
        ("pdf-split", "self-pair operation (pdf, pdf)"),
        ("xlsx-to-pdf", "plugin-less funnel page for (xlsx, pdf)"),
        ("pdf-to-xlsx", "plugin-less funnel page for (pdf, xlsx)"),
        ("pptx-to-pdf", "plugin-less funnel page for (pptx, pdf)"),
        ("pdf-to-pptx", "plugin-less funnel page for (pdf, pptx)"),
        ("png-to-pdf", "distinct product; (png, pdf) owned by images-to-pdf"),
    ):
        assert any(loc.endswith(f"/tools/{slug}") for loc in locations), (
            f"legitimate same-pair tool dropped from sitemap ({rationale}): {slug}"
        )
