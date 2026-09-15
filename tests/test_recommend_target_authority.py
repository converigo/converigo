"""RE — RecommendationEngine must never advertise a target the D5 authority cannot dispatch.

Why this file exists
--------------------
D5 made ``app/services/target_capability.py`` the single authority for what a user
may be offered, and rewired the homepage and the V2 tool-page widget to it. The
legacy tool-page target selector was left behind: ``RecommendationEngine`` builds
its chip list from ``registry.get_plugins_by_source(source)`` and
``scorer.build_option``'s ``plugin.target_formats[0]`` — a *source-keyed claim* —
while conversion dispatch is *operation-keyed*
(``registry.get_plugin(source, target, slug=operation)``). ``/convert`` from a
legacy tool page posts ``operation=<page slug>``
(``app/static/js/convert/converter.js``), so every chip whose pair the page's own
plugin does not claim dies as ``422 UNSUPPORTED_CONVERSION``. On top of that the
router invents a ``pdf`` chip for any source with no candidate at all, and the
engine re-adds the self-conversion and alias tokens D5 deliberately removed.

These tests lock the general invariant, not one symptom::

    ADVERTISED TARGET  ⊆  D5 DISPATCHABLE / CAPABLE TARGET

for every source the registry knows about, with and without operation context.
Pure Python + TestClient: no browser, no live server, no network.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.plugins.registry import registry
from app.recommendation.engine import recommendation_engine
from app.services.target_capability import (
    AUTO_DEFAULT_FIRST,
    PRODUCT_ALIAS_TOKENS,
    TARGET_CANONICAL,
    build_capability,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CARD_JS = (
    REPO_ROOT / "app" / "static" / "js" / "recommendation" / "recommendation_manager.js"
)

# Tokens D5 folds away or refuses to show. None of them may ever be a chip value.
BANNED_TARGET_TOKENS = set(TARGET_CANONICAL) | set(PRODUCT_ALIAS_TOKENS)

# Legacy tool pages whose content slug is not a registered plugin slug. They are a
# separate content/operation alignment problem (out of this scope); what this file
# pins is that they must fail *closed* — no chip, no 500, no dead dropdown entry.
CONTENT_ONLY_SLUGS = {
    "docx-to-pdf",
    "pdf-to-docx",
    "pdf-to-pptx",
    "pdf-to-xlsx",
    "pptx-to-pdf",
    "xlsx-to-pdf",
}

# Operation-scoped legacy pages: the card posts operation=<slug>, so the chip list
# must be bounded by what *that page* can dispatch.
OPERATION_PAGES = {
    "word-to-pdf": "docx",
    "pdf-compress": "pdf",
    "pdf-split": "pdf",
    "jpg-watermark": "jpg",
    "jpg-to-pdf": "jpg",
    "png-to-jpg": "png",
    "images-to-pdf": "png",
    "wav-to-mp3": "wav",
    "mp3-to-wav": "mp3",
    "gz-extract": "gz",
    "zip-extract": "zip",
    "tar-extract": "tar",
    "rar-extract": "rar",
    "7z-extract": "7z",
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def advertised(source: str, operation: str | None = None) -> list[str]:
    """Every target the legacy surface can put on screen, best choice first."""

    if operation is None:
        result = recommendation_engine.recommend(source)
    else:
        result = recommendation_engine.recommend(source, operation=operation)
    targets: list[str] = []
    if result.best_choice is not None:
        targets.append(str(result.best_choice.target))
    targets.extend(str(option.target) for option in result.alternatives)
    return targets


def authority_targets(source: str, operation: str | None = None) -> set[str]:
    """The D5 answer: what this source may be offered, optionally under an operation."""

    view = build_capability(operation).map
    return {target.lower() for target in view.get(source, [])}


def dispatchable(source: str, target: str, operation: str | None) -> bool:
    """Does /convert actually resolve a plugin for this chip, operation included?"""

    try:
        plugin = registry.get_plugin(source, target, slug=operation)
    except Exception:  # noqa: BLE001 - ValueError is the honest "cannot dispatch" answer
        return False
    return getattr(plugin, "advertisable", True) is not False


# ---------------------------------------------------------------------------
# 1. The general invariant, over every source the engine can be asked about.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source", sorted(registry.source_cache))
def test_advertised_targets_are_a_subset_of_d5_authority(source: str) -> None:
    allowed = authority_targets(source)
    out_of_authority = sorted(
        target for target in advertised(source) if target.lower() not in allowed
    )
    assert out_of_authority == [], (
        f"{source}: recommends {out_of_authority} which the D5 capability authority "
        f"does not contain (allowed={sorted(allowed)})"
    )


@pytest.mark.parametrize("source", sorted(registry.source_cache))
def test_every_advertised_pair_really_dispatches(source: str) -> None:
    """Authority membership is not enough: the pair must resolve for dispatch."""

    dead = [t for t in advertised(source) if not dispatchable(source, t, None)]
    assert dead == [], f"{source}: advertised pairs that cannot dispatch: {dead}"


@pytest.mark.parametrize("slug,source", sorted(OPERATION_PAGES.items()))
def test_operation_scoped_advertising_stays_dispatchable(
    slug: str, source: str
) -> None:
    """On a tool page the chip list is bounded by what *that page* can dispatch."""

    allowed = authority_targets(source, slug)
    for target in advertised(source, operation=slug):
        assert target.lower() in allowed, (
            f"/tools/{slug} offers {target!r} for {source!r}, outside the "
            f"operation-scoped authority {sorted(allowed)}"
        )
        assert dispatchable(source, target, slug), (
            f"/tools/{slug} offers {target!r} but get_plugin({source!r}, "
            f"{target!r}, slug={slug!r}) cannot dispatch it"
        )


# ---------------------------------------------------------------------------
# 2. Tokens D5 removed must not come back through the legacy surface.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source", sorted(registry.source_cache))
def test_no_self_conversion_is_advertised_without_operation(source: str) -> None:
    """Self-targets are operation-context only; the plain view must not carry them."""

    chips = [t for t in advertised(source) if t.lower() == source]
    assert chips == [], f"{source}: advertises a self-conversion with no operation context"


@pytest.mark.parametrize("source", sorted(registry.source_cache))
def test_no_alias_or_product_token_is_ever_advertised(source: str) -> None:
    """A chip value is the canonical extension the plugin actually delivers."""

    offenders = sorted({t for t in advertised(source) if t.lower() in BANNED_TARGET_TOKENS})
    assert offenders == [], f"{source}: advertises non-canonical token(s) {offenders}"


def test_office_sources_advertise_the_canonical_extension_not_ppt() -> None:
    """docx/xlsx/pdf really do produce a slide deck - the chip must say pptx."""

    for source in ("docx", "xlsx", "pdf"):
        chips = [c.lower() for c in advertised(source)]
        assert "ppt" not in chips, f"{source}: chip 'PPT' is not a deliverable extension"
        if "pptx" in authority_targets(source):
            assert "pptx" in chips, (
                f"{source}: pptx is dispatchable but the chip list lost it "
                f"(over-filtering: {chips})"
            )


# ---------------------------------------------------------------------------
# 3. No invented capability for a source nothing can convert.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source", ["word", "powerpoint", "spreadsheet", "xls", "ppt", "doc", "qqq"]
)
def test_unknown_or_non_uploadable_source_advertises_nothing(source: str) -> None:
    chips = advertised(source)
    assert chips == [], f"{source!r}: advertised {chips} although the authority has no row"


def test_endpoint_does_not_fabricate_a_fallback_target(client: TestClient) -> None:
    """The router used to inject a `pdf` chip for any source with no candidate."""

    for source in ("qqq", "word", "ppt"):
        response = client.get(f"/recommend/{source}")
        assert response.status_code == 200, f"/recommend/{source} must degrade, not 500"
        data = response.json()
        assert data["best_choice"] is None
        assert data["alternatives"] == [], (
            f"/recommend/{source} fabricated {data['alternatives']}"
        )


def test_endpoint_advertised_targets_match_the_authority_row(client: TestClient) -> None:
    allowed = authority_targets("pdf")
    response = client.get("/recommend/pdf")
    assert response.status_code == 200
    data = response.json()
    chips = [data["best_choice"]["target"]] + [i["target"] for i in data["alternatives"]]
    offenders = sorted(t for t in chips if t.lower() not in allowed)
    assert offenders == [], f"/recommend/pdf advertises {offenders} outside {sorted(allowed)}"


def test_operation_query_param_bounds_the_endpoint_payload(client: TestClient) -> None:
    """`/recommend/pdf?operation=pdf-compress` must not offer conversion chips."""

    response = client.get("/recommend/pdf", params={"operation": "pdf-compress"})
    assert response.status_code == 200
    data = response.json()
    chips: list[str] = []
    if data["best_choice"]:
        chips.append(data["best_choice"]["target"])
    chips.extend(item["target"] for item in data["alternatives"])
    for target in chips:
        assert dispatchable("pdf", target, "pdf-compress"), (
            f"/recommend/pdf?operation=pdf-compress offers {target!r}, which resolves "
            f"to 422 UNSUPPORTED_CONVERSION on that page"
        )
    assert "docx" not in [c.lower() for c in chips], (
        "pdf-compress must not advertise a conversion its own operation does not claim"
    )


@pytest.mark.parametrize(
    "slug,token",
    [
        ("gz-extract", "gz"),
        ("zip-extract", "zip"),
        ("tar-extract", "tar"),
        ("rar-extract", "rar"),
        ("7z-extract", "7z"),
    ],
)
def test_extract_pages_keep_their_legitimate_self_target(slug: str, token: str) -> None:
    """The archive extracts are the one place a self-target is honest; it must stay."""

    chips = [c.lower() for c in advertised(token, operation=slug)]
    assert token in chips, f"/tools/{slug} lost its own {token.upper()} action (got {chips})"
    assert set(chips) <= authority_targets(token, slug)


# ---------------------------------------------------------------------------
# 4. Chip provenance: the copy must describe the converter that will run.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "slug,source", [("jpg-watermark", "jpg"), ("pdf-compress", "pdf"), ("pdf-split", "pdf")]
)
def test_chip_metadata_comes_from_the_dispatch_winning_plugin(
    client: TestClient, slug: str, source: str
) -> None:
    """`jpg -> jpg` on the watermark page was titled "JPG Compress" and ran
    JPG Watermark; the chip said Compress, the file came back watermarked."""

    winner = registry.get_plugin(source, source, slug=slug)
    response = client.get(f"/recommend/{source}", params={"operation": slug})
    assert response.status_code == 200
    data = response.json()
    chips = ([data["best_choice"]] if data["best_choice"] else []) + list(data["alternatives"])
    matching = [c for c in chips if str(c["target"]).lower() == source]
    assert matching, f"{slug}: self-target chip missing from {chips}"
    assert matching[0]["title"] == winner.name, (
        f"{slug}: chip titled {matching[0]['title']!r} but "
        f"get_plugin({source!r}, {source!r}, slug={slug!r}) runs {winner.name!r}"
    )
    assert matching[0]["score"] == pytest.approx(
        recommendation_engine.scorer.calculate(winner)
    ), f"{slug}: chip score does not describe the plugin that will run"


# ---------------------------------------------------------------------------
# 5. Fail-closed and honest: known-bad content slugs, and junk input.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(CONTENT_ONLY_SLUGS))
def test_content_only_pages_fail_closed_instead_of_advertising_dead_chips(
    client: TestClient, slug: str
) -> None:
    source = slug.split("-to-")[0]
    response = client.get(f"/recommend/{source}", params={"operation": slug})
    assert response.status_code == 200
    data = response.json()
    chips = ([data["best_choice"]] if data["best_choice"] else []) + list(data["alternatives"])
    for chip in chips:
        assert dispatchable(source, str(chip["target"]).lower(), slug), (
            f"/tools/{slug} offers {chip['target']!r}, which always 422s"
        )


@pytest.mark.parametrize(
    "operation", ["not-a-real-operation", "../../etc/passwd", "PDF-COMPRESS"]
)
def test_junk_operation_never_500s_or_leaks(client: TestClient, operation: str) -> None:
    response = client.get("/recommend/pdf", params={"operation": operation})
    assert response.status_code == 200, "an unknown operation must fail closed, not error"
    text = response.text.lower()
    for needle in ("traceback", "valueerror", "not registered", "c:\\", "/app/"):
        assert needle not in text, f"{needle!r} leaked into the /recommend payload"
    data = response.json()
    chips = ([data["best_choice"]] if data["best_choice"] else []) + list(
        data["alternatives"]
    )
    for chip in chips:
        assert dispatchable("pdf", str(chip["target"]).lower(), operation), (
            f"operation={operation!r} advertised undispatchable {chip['target']!r}"
        )


def test_oversized_operation_is_bounded_not_crashed(client: TestClient) -> None:
    """A 300-character slug is input-validation territory: bounded, never a 5xx."""

    response = client.get("/recommend/pdf", params={"operation": "x" * 300})
    assert response.status_code in (200, 422), (
        f"oversized operation produced {response.status_code}"
    )
    assert response.status_code < 500


# ---------------------------------------------------------------------------
# 6. Real capability must survive: the gate may narrow, never hollow out.
# ---------------------------------------------------------------------------


def test_valid_recommendations_survive_the_authority_gate() -> None:
    assert advertised("docx")[0].lower() == "pdf", "Word -> PDF must stay the top pick"
    assert advertised("jpg")[0].lower() == "webp", "JPG -> WEBP must stay the top pick"
    assert {c.lower() for c in advertised("wav")} == {"mp3", "flac", "aac"}
    assert {c.lower() for c in advertised("mp3")} == {"wav", "aac"}
    xlsx_chips = {c.lower() for c in advertised("xlsx")}
    assert {"pdf", "csv", "json"} <= xlsx_chips, f"Excel picks hollowed out: {xlsx_chips}"


def test_recommendation_ordering_remains_score_ranked() -> None:
    result = recommendation_engine.recommend("pdf")
    chips = [result.best_choice, *result.alternatives]
    scores = [c.score for c in chips]
    assert scores == sorted(scores, reverse=True), f"not score-ranked: {scores}"
    assert len({str(c.target).lower() for c in chips}) == len(scores), "duplicate target chips"


def test_first_chip_follows_the_authority_default_and_the_rest_stays_scored() -> None:
    """Position zero is a default-target policy, not a ranking result.

    ``renderFormats()`` auto-selects the first chip, so the authority's pinned
    default must lead; the engine keeps ranking what follows. Without this, a
    ``.wav`` upload silently defaults to AAC - the regression WS1 fixed on the
    homepage - because score alone outranks MP3.
    """

    for source, pinned in AUTO_DEFAULT_FIRST.items():
        result = recommendation_engine.recommend(source)
        chips = [result.best_choice, *result.alternatives]
        assert chips, f"{source} lost every recommendation"
        assert str(chips[0].target).lower() == pinned, (
            f"{source}: first chip is {chips[0].target!r}, but the capability "
            f"authority pins {pinned!r} as the default target"
        )
        rest = [c.score for c in chips[1:]]
        assert rest == sorted(rest, reverse=True), (
            f"{source}: tail stopped being score-ranked: {rest}"
        )


# ---------------------------------------------------------------------------
# 7. The legacy card must ask for the same operation context it posts on /convert.
# ---------------------------------------------------------------------------


def test_legacy_card_fetches_recommendation_with_its_page_operation() -> None:
    """converter.js posts operation=<slug>; the recommendation fetch must request
    the same context, or the chip list is bounded by the wrong authority."""

    source = CARD_JS.read_text(encoding="utf-8")
    assert re.search(r"/recommend/", source), "legacy card no longer calls /recommend"
    assert re.search(r"operation", source), (
        "recommendation_manager.js must pass the page operation to /recommend so the "
        "chip list is bounded by the operation-scoped authority"
    )
    assert re.search(r"pathParts\[0\]\s*===\s*[\"']tools[\"']", source) or re.search(
        r"dataset\.operation", source
    ), "the operation must be derived from the /tools/<slug> page context"

