"""P2.2 — slug-aware fallback: `images-to-pdf` surfaces as a supported converter.

Context
-------
`images-to-pdf` declares ``source: "image"`` (a *category*, not a concrete
format), so the pair lookup ``plugin_registry.get_plugin("image", "pdf")``
raises ``ValueError`` and the converter used to be dropped from every public
surface.  P2.2 adds a fail-closed, slug-aware fallback in
``ConverterDataService._is_supported_converter``.

These tests pin that behaviour:
  * the fallback accepts a registered slug and rejects non-production-ready
    (NPR), search-index-disabled (SID) and unknown slugs;
  * `images-to-pdf` shows up in supported/public listings, the popular
    superset, the image + pdf hubs and the sitemap (exactly once);
  * unrelated converters (`pdf-merge`, `pdf-compress`) are unchanged.

The ``/tools`` directory has a *pre-existing* per-category display cap
(``sorted(...)[:5]``) that keeps `images-to-pdf` out of the top-5 image
cards.  That cap is untouched by P2.2 and is documented — not fixed — here.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from app.plugins.registry import registry as plugin_registry
from app.routers.tools import (
    _normalize_directory_category,
    _sort_tools_for_directory,
)
from app.services.converter_data_service import (
    NON_PRODUCTION_READY_SLUGS,
    SEARCH_INDEX_DISABLED_SLUGS,
    ConverterDataService,
)
from app.services.hub_service import HubService
from app.services.related_converter_service import RelatedConverterService

DATA_DIR = Path("app/data/converters")
SLUG = "images-to-pdf"


@pytest.fixture(scope="module")
def service() -> ConverterDataService:
    return ConverterDataService(DATA_DIR)


def _write_converter(path: Path, slug: str, **kwargs: object) -> None:
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


# ---------------------------------------------------------------------------
# Fail-closed fallback (isolated, deterministic)
# ---------------------------------------------------------------------------


def test_slug_fallback_accepts_registered_slug_with_category_source(tmp_path: Path) -> None:
    """A category-valued ``source`` is accepted when the slug is registered."""
    assert plugin_registry.has_slug(SLUG) is True
    _write_converter(
        tmp_path / f"{SLUG}.json",
        slug=SLUG,
        source="image",  # category, not a concrete format
        target="pdf",
    )

    supported = {
        converter["slug"] for converter in ConverterDataService(tmp_path).list_supported_converters()
    }
    assert SLUG in supported


@pytest.mark.parametrize("slug", sorted(NON_PRODUCTION_READY_SLUGS))
def test_slug_fallback_rejects_non_production_ready_slugs(tmp_path: Path, slug: str) -> None:
    """NPR slugs are rejected by the fallback when it is the resolution path.

    Note: not every NPR slug is a registered plugin (``heif-to-jpeg`` and
    ``svg-to-pdf`` are not), and registered NPR slugs may still be reached via
    the *pair* lookup (e.g. ``7z-extract``).  Here ``source`` is a category, so
    the pair lookup cannot succeed and the fallback must fail closed.
    """
    _write_converter(tmp_path / f"{slug}.json", slug=slug, source="image", target="pdf")

    supported = {
        converter["slug"] for converter in ConverterDataService(tmp_path).list_supported_converters()
    }
    assert slug not in supported


@pytest.mark.parametrize("slug", sorted(SEARCH_INDEX_DISABLED_SLUGS))
def test_slug_fallback_rejects_search_index_disabled_slugs(tmp_path: Path, slug: str) -> None:
    """SID slugs stay filtered even though the plugin slug is registered."""
    assert plugin_registry.has_slug(slug) is True
    _write_converter(tmp_path / f"{slug}.json", slug=slug, source="image", target="pdf")

    supported = {
        converter["slug"] for converter in ConverterDataService(tmp_path).list_supported_converters()
    }
    assert slug not in supported


def test_slug_fallback_rejects_unregistered_slug(tmp_path: Path) -> None:
    """An unknown slug is not rescued by the fallback."""
    _write_converter(
        tmp_path / "totally-made-up-xyz.json",
        slug="totally-made-up-xyz",
        source="image",
        target="pdf",
    )

    supported = {
        converter["slug"] for converter in ConverterDataService(tmp_path).list_supported_converters()
    }
    assert "totally-made-up-xyz" not in supported


def test_pair_lookup_path_still_filters_unknown_pairs(tmp_path: Path) -> None:
    """The original pair-lookup rejection (magic-to-pdf) is unchanged."""
    _write_converter(tmp_path / "magic-to-pdf.json", slug="magic-to-pdf", source="magic", target="pdf")
    _write_converter(tmp_path / "jpg-to-png.json", slug="jpg-to-png", source="jpg", target="png")

    supported = {
        converter["slug"] for converter in ConverterDataService(tmp_path).list_supported_converters()
    }
    assert "jpg-to-png" in supported
    assert "magic-to-pdf" not in supported


# ---------------------------------------------------------------------------
# Real-data surfacing
# ---------------------------------------------------------------------------


def test_images_to_pdf_in_supported_and_public_listings(service: ConverterDataService) -> None:
    assert SLUG in {c["slug"] for c in service.list_supported_converters()}
    assert SLUG in {c["slug"] for c in service.list_public_converters()}


def test_images_to_pdf_in_popular_superset(service: ConverterDataService) -> None:
    """It is marked popular and present in the popular superset.

    It is not in the top-6 home grid, which is a data/ranking outcome
    (many featured tools outrank it), not a filtering regression.
    """
    popular_all = {c["slug"] for c in service.list_popular_converters(limit=9999)}
    assert SLUG in popular_all


@pytest.mark.parametrize("hub_slug", ["image-conversion", "pdf-conversion"])
def test_images_to_pdf_in_hubs(service: ConverterDataService, hub_slug: str) -> None:
    hub = HubService(service).get_hub_page_data(hub_slug)
    all_slugs = {c["slug"] for c in hub.get("all_converters", [])}
    assert SLUG in all_slugs


def test_tools_directory_groups_images_to_pdf_into_image_category() -> None:
    """The directory *grouping* classifies it correctly."""
    converter = ConverterDataService(DATA_DIR).load_converter_by_slug(SLUG)
    assert _normalize_directory_category(converter) == "image"


def test_tools_directory_category_cap_documents_preexisting_limit(service: ConverterDataService) -> None:
    """Documents a *pre-existing* display cap, unrelated to P2.2.

    ``_build_tools_directory_categories`` renders only the first five tools of
    each category (``sorted(...)[:5]``).  ``images-to-pdf`` is a non-featured
    popular tool, so it sorts to index 5 and is cut.  P2.2 does not change this
    cap; this test records the current behaviour so the limitation is explicit.
    """
    image_tools = [
        tool for tool in service.list_supported_converters()
        if _normalize_directory_category(tool) == "image"
    ]
    image_tools.sort(key=_sort_tools_for_directory)
    top5 = [tool["slug"] for tool in image_tools[:5]]

    assert SLUG in {tool["slug"] for tool in image_tools}  # it is in the group
    assert SLUG not in top5  # but the [:5] cap hides it from the directory


@pytest.mark.parametrize("origin", ["txt-to-pdf", "jpg-to-pdf", "pdf-merge"])
def test_related_tools_includes_images_to_pdf_at_high_limit(
    service: ConverterDataService, origin: str
) -> None:
    """Related listings surface it once the limit is not truncated to 4."""
    related_service = RelatedConverterService(service)
    origin_converter = service.load_converter_by_slug(origin)
    slugs = {c["slug"] for c in related_service.get_related_converters(origin_converter, limit=200)}
    assert SLUG in slugs


def test_images_to_pdf_related_tools_are_non_empty(service: ConverterDataService) -> None:
    """Its own related block renders (default limit=4)."""
    converter = service.load_converter_by_slug(SLUG)
    related = RelatedConverterService(service).get_related_converters(converter, limit=4)
    assert len(related) == 4


def test_sitemap_contains_images_to_pdf_exactly_once(service: ConverterDataService) -> None:
    entries = service.sitemap_entries("https://converigo.com")
    tool_slugs = [e["loc"].split("/tools/")[-1] for e in entries if "/tools/" in e["loc"]]

    counts = Counter(tool_slugs)
    assert counts[SLUG] == 1
    assert [slug for slug, n in counts.items() if n > 1] == []

    # De-index (SID) slugs must never be advertised to crawlers.
    assert not (set(tool_slugs) & SEARCH_INDEX_DISABLED_SLUGS)

    # NPR slugs may legitimately appear: `7z-extract`, `heic-to-jpg` and
    # `svg-to-png` resolve through the pair lookup, which does not consult the
    # NPR set.  Pin the observed set so future drift is visible (P2.2 does not
    # change this behaviour; it is recorded, not fixed, here).
    assert (set(tool_slugs) & NON_PRODUCTION_READY_SLUGS) == {
        "7z-extract",
        "heic-to-jpg",
        "svg-to-png",
    }


def test_pdf_merge_and_pdf_compress_unchanged(service: ConverterDataService) -> None:
    supported = {c["slug"] for c in service.list_supported_converters()}
    public = {c["slug"] for c in service.list_public_converters()}

    assert "pdf-merge" in supported and "pdf-merge" in public
    assert "pdf-compress" in supported and "pdf-compress" in public