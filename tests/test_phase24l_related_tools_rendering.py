"""Phase 24L: related-tools Section A empty-slug rendering regression tests.

Root cause reproduced by Phase 24K and fixed in Phase 24L:
``InternalLinkService._score_and_format_converters`` emitted items without a
``slug`` key, while the tool-page related-tools template renders
``href="/tools/{{ related.slug }}"``. Every Section A card therefore collapsed
to the bare ``/tools/`` index (5 duplicate empty-slug hrefs per tool page).
"""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.internal_link_service import InternalLinkService

CONVERTERS_DIR = Path("app/data/converters")


def _section_cards(html: str, section_id: str) -> list[tuple[str, str]]:
    """Return (href, anchor) pairs from the first section with the given id."""
    match = re.search(rf'id="{section_id}"(.*?)</section>', html, re.S)
    assert match, f"page is missing #{section_id} section"
    return re.findall(r'<h3><a href="([^"]*)">([^<]*)</a></h3>', match.group(1))


class TestScoreAndFormatConverterShape:
    """Producer-level: _score_and_format_converters must emit a usable slug."""

    def test_items_include_nonempty_slug_matching_href(self) -> None:
        service = InternalLinkService(CONVERTERS_DIR)
        items = service._score_and_format_converters(
            [{"slug": "pdf-to-png", "description": "Convert PDFs."}]
        )
        assert items, "expected at least one formatted converter"
        for item in items:
            assert item["slug"], "slug must be non-empty"
            assert item["href"] == f"/tools/{item['slug']}"

    def test_empty_slug_converter_is_skipped(self) -> None:
        """A converter without slug must never yield an empty-slug /tools/ href."""
        service = InternalLinkService(CONVERTERS_DIR)
        assert service._score_and_format_converters([{"title": "No slug"}]) == []

    def test_exclude_slug_still_filters_self_reference(self) -> None:
        service = InternalLinkService(CONVERTERS_DIR)
        items = service._score_and_format_converters(
            [{"slug": "pdf-to-png"}, {"slug": "pdf-to-word"}],
            exclude_slug="pdf-to-png",
        )
        assert [item["slug"] for item in items] == ["pdf-to-word"]


class TestToolPageSectionARendering:
    """Page-level: the production-like failing case (/tools/pdf-to-jpg)."""

    def test_no_empty_slug_related_href(self) -> None:
        """Verification 1: no Section A href equals the bare /tools/ index."""
        client = TestClient(app)
        html = client.get("/tools/pdf-to-jpg").text
        hrefs = [href for href, _ in _section_cards(html, "related-tools")]
        assert hrefs, "expected related-tools cards on /tools/pdf-to-jpg"
        assert "/tools/" not in hrefs, "empty-slug related href rendered"

    def test_section_a_hrefs_are_unique_valid_and_live_in_registry(self) -> None:
        """Verifications 2+3: valid, distinct hrefs from the fixed path."""
        client = TestClient(app)
        html = client.get("/tools/pdf-to-jpg").text
        hrefs = [href for href, _ in _section_cards(html, "related-tools")]
        assert len(hrefs) == len(set(hrefs)), f"duplicate related hrefs: {hrefs}"
        for href in hrefs:
            assert re.fullmatch(r"/tools/[a-z0-9][a-z0-9-]*", href), f"bad href: {href}"
            slug = href.removeprefix("/tools/")
            assert (CONVERTERS_DIR / f"{slug}.json").exists(), (
                f"related target {slug} has no converter record"
            )

    def test_valid_related_cards_still_render_in_both_sections(self) -> None:
        """Verification 2: Section B coverage intact; Section A now valid too."""
        client = TestClient(app)
        html = client.get("/tools/pdf-to-jpg").text
        section_b = _section_cards(html, "related-converters")
        assert len(section_b) >= 1
        for href, _ in section_b:
            assert re.fullmatch(r"/tools/[a-z0-9][a-z0-9-]*", href), f"bad href: {href}"
        section_a = _section_cards(html, "related-tools")
        assert len(section_a) == 5

    def test_single_related_tools_section_id_and_hero_anchor_intact(self) -> None:
        """Duplicate id=related-tools removed; hero #related-tools anchor kept."""
        client = TestClient(app)
        html = client.get("/tools/pdf-to-jpg").text
        assert html.count('id="related-tools"') == 1
        assert 'id="related-converters"' in html
        assert 'href="#related-tools"' in html
