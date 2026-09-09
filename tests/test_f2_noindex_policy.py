"""G1-3 F-2 — ledger-driven temporary noindex policy for deprecated converters.

Policy under test (source of truth: certification ledger
``app/data/certified_converters.json``, ``disabled`` group with
``lifecycle_status == "deprecated"``):

1. /tools/<slug> pages of deprecated converters emit ``robots: noindex,follow``.
2. Deprecated converters are excluded from sitemap entries (209 -> 205 with
   the current data; 204 pre-G1-5 plus the G1-5 F-7 data-conversion hub loc), while the G1-1 F-3 residue pairs stay included.
3. Hub pages keep every converter anchor but flag deprecated converters with
   a localized "Coming soon" badge.

The suite pins the current five deprecated slugs; adding/removing a slug in
the ledger is an intentional policy change that must update the set here.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.tools import apply_search_index_policy
from app.services.converter_data_service import (
    SEARCH_INDEX_DISABLED_SLUGS,
    ConverterDataService,
)
from app.services.converter_registry_service import ConverterRegistryService
from app.services.hub_service import HubService
from app.services.plugin_validation_service import PluginValidationService

F2_DEPRECATED_SLUGS = {
    "docx-to-ppt",
    "docx-to-xlsx",
    "ppt-to-docx",
    "ppt-to-xlsx",
    "xlsx-to-ods",
}
CONTROL_SLUGS = ["docx-to-pdf", "xlsx-to-docx"]
CONVERTERS_DIR = Path("app/data/converters")
EXPECTED_SITEMAP_COUNT = 205  # 209 pre-F-2 entries minus the 5 deprecated slugs, plus the G1-5 F-7 data-conversion hub


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# §0 — ledger derivation
# ---------------------------------------------------------------------------


def test_derived_disabled_slugs_match_ledger_and_f2_set() -> None:
    recomputed = ConverterRegistryService.get_search_index_disabled_slugs(CONVERTERS_DIR)
    assert recomputed == SEARCH_INDEX_DISABLED_SLUGS
    assert recomputed == F2_DEPRECATED_SLUGS


def test_ledger_derivation_selects_only_deprecated_entries(tmp_path: Path) -> None:
    ledger = {
        "certified": [{"slug": "jpg-to-png", "lifecycle_status": "certified"}],
        "beta": [{"slug": "beta-tool", "lifecycle_status": "beta"}],
        "disabled": [
            {"slug": "docx-to-ppt", "lifecycle_status": "deprecated"},
            {"slug": "recertified-tool", "lifecycle_status": "active"},
            {"slug": "beta-in-disabled", "lifecycle_status": "beta"},
            {"slug": "", "lifecycle_status": "deprecated"},
            {"lifecycle_status": "deprecated"},
            "not-a-dict",
        ],
    }
    (tmp_path / "certified_converters.json").write_text(json.dumps(ledger), encoding="utf-8")
    # The helper resolves the ledger as the parent of the contracts dir.
    contracts_dir = tmp_path / "converters"
    contracts_dir.mkdir()

    assert ConverterRegistryService.get_search_index_disabled_slugs(contracts_dir) == {"docx-to-ppt"}


@pytest.mark.parametrize("ledger_payload", [None, "{not json", {"certified": [], "beta": []}])
def test_ledger_derivation_fails_open(tmp_path: Path, ledger_payload) -> None:
    ledger_path = tmp_path / "certified_converters.json"
    if ledger_payload is not None:
        content = ledger_payload if isinstance(ledger_payload, str) else json.dumps(ledger_payload)
        ledger_path.write_text(content, encoding="utf-8")
    contracts_dir = tmp_path / "converters"
    contracts_dir.mkdir()

    assert ConverterRegistryService.get_search_index_disabled_slugs(contracts_dir) == set()


# ---------------------------------------------------------------------------
# §1 — robots noindex,follow on tool pages
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(F2_DEPRECATED_SLUGS))
def test_deprecated_tool_pages_emit_noindex_follow(client: TestClient, slug: str) -> None:
    response = client.get(f"/tools/{slug}")

    assert response.status_code == 200
    assert '<meta name="robots" content="noindex,follow">' in response.text


@pytest.mark.parametrize("slug", CONTROL_SLUGS)
def test_control_tool_pages_keep_index_follow(client: TestClient, slug: str) -> None:
    response = client.get(f"/tools/{slug}")

    assert response.status_code == 200
    assert '<meta name="robots" content="index,follow">' in response.text


def test_noindex_policy_wins_over_meta_overrides() -> None:
    seo_data = apply_search_index_policy({"robots": "index,follow"}, "docx-to-ppt")
    assert seo_data["robots"] == "noindex,follow"

    untouched = {"robots": "noindex,nofollow"}
    seo_data = apply_search_index_policy(untouched, "docx-to-pdf")
    assert seo_data["robots"] == "noindex,nofollow"  # only narrows, never widens


# ---------------------------------------------------------------------------
# §2 — sitemap exclusion (209 -> 204), F-3 pairs intact
# ---------------------------------------------------------------------------


def test_sitemap_excludes_deprecated_slugs_and_keeps_counts(client: TestClient) -> None:
    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    locs = [loc.rstrip("/") for loc in _extract_locs(response.text)]
    assert len(locs) == EXPECTED_SITEMAP_COUNT
    for slug in F2_DEPRECATED_SLUGS:
        assert f"https://converigo.com/tools/{slug}" not in locs
    # Homepage and trust pages are unaffected by the policy.
    for path in ("/", "/about", "/privacy-policy", "/terms", "/contact", "/cookies"):
        assert f"https://converigo.com{path}".rstrip("/") in locs


@pytest.mark.parametrize(
    "slug",
    sorted(F2_DEPRECATED_SLUGS) + ["pdf-merge", "images-to-pdf", *CONTROL_SLUGS],
)
def test_sitemap_entries_filter_is_scoped_to_deprecated_slugs(slug: str) -> None:
    entries = ConverterDataService(CONVERTERS_DIR).sitemap_entries("https://converigo.com")
    locs = {entry["loc"].rstrip("/") for entry in entries}

    if slug in F2_DEPRECATED_SLUGS:
        assert f"https://converigo.com/tools/{slug}" not in locs
    else:
        # G1-1 F-3 residue pairs and active controls stay listed.
        assert f"https://converigo.com/tools/{slug}" in locs


# ---------------------------------------------------------------------------
# §2 ripple — plugin validation stays green for deprecated slugs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(F2_DEPRECATED_SLUGS) + CONTROL_SLUGS)
def test_validate_sitemap_accepts_policy_state(slug: str) -> None:
    service = PluginValidationService(CONVERTERS_DIR)
    result = service.validate_converter(slug)

    assert result.checks.get("sitemap_valid") is True
    assert not any("not found in sitemap entries" in error for error in result.errors)


# ---------------------------------------------------------------------------
# §3 — hub anchors preserved, "Coming soon" badges added
# ---------------------------------------------------------------------------


def test_hub_page_keeps_all_anchors_and_adds_badges(client: TestClient) -> None:
    response = client.get("/document-conversion")

    assert response.status_code == 200
    html = response.text
    expected_anchors = {
        "docx-to-ppt": 2,
        "docx-to-xlsx": 2,
        "ppt-to-docx": 1,
        "ppt-to-xlsx": 1,
        "xlsx-to-ods": 1,
    }
    for slug, count in expected_anchors.items():
        assert html.count(f'href="/tools/{slug}"') == count, slug
    assert html.count("tool-card-badge") == len(F2_DEPRECATED_SLUGS)
    # Control converters keep their anchors and never get a badge.
    assert html.count('href="/tools/docx-to-pdf"') >= 1
    for chunk in html.split('href="/tools/docx-to-pdf"')[1:]:
        assert "tool-card-badge" not in chunk[:200]


def test_hub_service_flags_not_available_for_deprecated_only() -> None:
    service = HubService(ConverterDataService(CONVERTERS_DIR))
    page_data = service.get_hub_page_data("document-conversion")

    flagged: set[str] = set()
    for section in ("featured_converters", "popular_converters", "related_converters", "all_converters"):
        for tool in page_data[section]:
            assert isinstance(tool["not_available"], bool)
            if tool["not_available"]:
                flagged.add(tool["slug"])
                assert tool["slug"] in F2_DEPRECATED_SLUGS

    assert flagged == F2_DEPRECATED_SLUGS


def _extract_locs(sitemap_xml: str) -> list[str]:
    import re

    return re.findall(r"<loc>(.*?)</loc>", sitemap_xml)
