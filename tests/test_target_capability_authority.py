"""D5 integrity: ONE authoritative conversion capability, BOTH UI consumers.

Why this file exists
--------------------
The homepage (``app/templates/main/converigo_main.html``) and the tool-page
result widget (``app/static/js/widgets/tool_result_widget_v2.js``) each carried a
hand-maintained ``STATIC_TARGET_MAP`` literal. Nothing enforced that either
literal matched what ``PluginRegistry`` can actually dispatch, so both drifted:
``pdf -> WORD`` stayed on screen long after the only plugin able to claim it
became an honest-failure placeholder, the widget still advertised ``.doc``/
``.xls``/``.ppt`` source rows that PR-1 had already disabled, and whole rows were
keyed on tokens (``word``, ``powerpoint``, ``spreadsheet``) that the upload
validator rejects, so they could never be reached.

The pre-existing parity coverage could not catch any of that:
``tests/test_ui_target_mapping.py`` derived its expectation from plugin
``source_formats x target_formats`` (the *claim*, not the dispatch, alias tokens
included) and needed Playwright plus a live server; ``test_globalfmt_intersection
.py`` asserted a frozen "Phase A matrix" answer and was both stale and
browser-gated (its png+m4a case is nested inside another test, so it never ran).

This suite is deliberately pure Python: no browser, no Node, no live server.
``fastapi.testclient.TestClient`` renders the pages the way production does, so
the assertions run against the HTML actually shipped, compared with
``app.services.target_capability`` - the single derived source - and with the
registry's own dispatch index. Zero false positives and zero false negatives are
both asserted, so the cutover can neither advertise a dead option nor quietly
drop a converter that really works.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.plugins.registry import registry
from app.services.target_capability import (
    PRODUCT_ALIAS_TOKENS,
    TARGET_CANONICAL,
    build_capability,
    conversion_capability,
)
from app.utils.file_validator import ALLOWED_EXTENSIONS

REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_TEMPLATE = REPO_ROOT / "app" / "templates" / "main" / "converigo_main.html"
WIDGET_JS = REPO_ROOT / "app" / "static" / "js" / "widgets" / "tool_result_widget_v2.js"
ROUTER_HOME = REPO_ROOT / "app" / "routers" / "home.py"

# Same shape the WS1 safety test uses on the served homepage document.
_MAP_BLOCK_RE = re.compile(r"const STATIC_TARGET_MAP = \{(.*?)\};", re.S)
_ENTRY_RE = re.compile(r'"?([A-Za-z0-9_]+)"?\s*:\s*\[([^\]]*)\]')

EXTENSION_SHAPE = re.compile(r"^[a-z0-9]{1,8}$")

EXTRACT_OPERATIONS = {
    "tar-extract": "tar",
    "zip-extract": "zip",
    "gz-extract": "gz",
    "rar-extract": "rar",
    "7z-extract": "7z",
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _parsed_values(raw: str) -> list[str]:
    return [item.strip().strip("\"'") for item in raw.split(",") if item.strip()]


def served_homepage_map(client: TestClient) -> dict[str, list[str]]:
    """The target picker the homepage actually ships, parsed from served HTML."""

    response = client.get("/")
    assert response.status_code == 200
    match = _MAP_BLOCK_RE.search(response.text)
    assert match, "no `const STATIC_TARGET_MAP = {...}` found in the served homepage"
    return {
        key.lower(): _parsed_values(values)
        for key, values in _ENTRY_RE.findall(match.group(1))
    }


def served_widget_map(client: TestClient, slug: str) -> dict[str, list[str]]:
    """The target picker the V2 widget actually ships for a mounted operation."""

    response = client.get(f"/tools/{slug}")
    assert response.status_code == 200
    match = re.search(r'data-target-map="(?P<payload>[^"]*)"', response.text)
    assert match, (
        f"/tools/{slug}: the widget mount exposes no data-target-map, so the "
        "component still has to fall back to a hardcoded map"
    )
    payload = html.unescape(match.group("payload"))
    return {
        key.lower(): [str(value).upper() for value in values]
        for key, values in json.loads(payload).items()
    }


def dispatchable_pairs() -> set[tuple[str, str]]:
    return set(registry.plugins.keys())


def advertisable_pairs() -> set[tuple[str, str]]:
    return {
        pair
        for pair, plugin in registry.plugins.items()
        if getattr(plugin, "advertisable", True) is not False
    }


# ---------------------------------------------------------------------------
# 1. The authority itself.
# ---------------------------------------------------------------------------


def test_capability_is_derived_from_the_real_dispatch_index() -> None:
    """0 FP: every advertised pair really resolves to an advertisable plugin."""

    for source, targets in conversion_capability().items():
        for target in targets:
            pair = (source, target.lower())
            assert pair in dispatchable_pairs(), (
                f"{source}->{target} is advertised but PluginRegistry.get_plugin() "
                "would raise: the UI would send a doomed request"
            )
            assert pair in advertisable_pairs(), (
                f"{source}->{target} is advertised but its winning plugin is not "
                "advertisable (placeholder-backed capability)"
            )


def test_capability_drops_no_real_conversion() -> None:
    """0 FN: every uploadable, advertisable, non-self pair is offered."""

    view = conversion_capability()
    for source, target in sorted(advertisable_pairs()):
        if source not in ALLOWED_EXTENSIONS:
            continue  # cannot be uploaded, so it can never start a conversion
        if source == target:
            continue  # format-preserving operation: operation-context only
        expected = TARGET_CANONICAL.get(target, target)
        assert expected.upper() in view.get(source, []), (
            f"{source}->{target} dispatches for real but is not advertised "
            f"(expected canonical option {expected.upper()})"
        )


def test_rejections_are_only_the_known_placeholder_pairs() -> None:
    view = build_capability()
    assert view.rejections == [
        "pdf->word: winning plugin is not advertisable",
        "word->pdf: winning plugin is not advertisable",
    ], f"unexpected capability rejections: {view.rejections}"


def test_placeholders_stay_registered_but_are_not_advertisable() -> None:
    """D5 removes placeholders from discovery only; PR-0 honesty is intact."""

    from app.plugins.document.office_conversion_plugins import (
        PDFToWordPlugin,
        WordToPDFPlugin,
        _OfficePlaceholderPlugin,
    )

    assert _OfficePlaceholderPlugin.advertisable is False
    assert PDFToWordPlugin.advertisable is False
    assert WordToPDFPlugin.advertisable is False
    # Still registered: the legacy pair path resolves to the placeholder so
    # /convert answers UNSUPPORTED_CONVERSION ("coming soon") instead of a 404
    # for anyone who bookmarked the operation. D5 must not change that.
    assert registry.get_plugin("pdf", "word").advertisable is False
    assert registry.get_plugin("word", "pdf").advertisable is False
    # The real winner still owns the pairs it declares.
    assert registry.get_plugin("pdf", "doc").advertisable is True

    # And the D4 guard is untouched: a slug-aware request is authorized only by
    # the winning plugin's own claim set, so pdf-to-word refuses target=word.
    with pytest.raises(ValueError):
        registry.get_plugin("pdf", "word", slug="pdf-to-word")
    with pytest.raises(ValueError):
        registry.get_plugin("word", "pdf", slug="word-to-pdf")


def test_real_office_converters_are_not_over_excluded() -> None:
    assert registry.plugins[("pptx", "docx")].advertisable is True
    assert registry.plugins[("docx", "pptx")].advertisable is True
    assert registry.plugins[("pdf", "docx")].advertisable is True


# ---------------------------------------------------------------------------
# 2. What a user may be shown: canonical extensions, never product aliases.
# ---------------------------------------------------------------------------


def test_option_values_are_canonical_extensions_only() -> None:
    view = conversion_capability()
    offenders = {
        f"{source}.{target}"
        for source, targets in view.items()
        for target in targets
        if target.lower() in PRODUCT_ALIAS_TOKENS
        or not EXTENSION_SHAPE.match(target.lower())
    }
    assert not offenders, (
        "user-facing option values must be the canonical extension the winning "
        f"plugin delivers; found non-extension/product-alias values: {sorted(offenders)}"
    )


def test_legacy_ole2_extension_tokens_are_not_user_facing_targets() -> None:
    """doc/xls/ppt fold to the OOXML form that is actually written out."""

    view = conversion_capability()
    stale = {
        f"{source}.{target}"
        for source, targets in view.items()
        for target in targets
        if target.lower() in {"doc", "xls", "ppt"}
    }
    assert not stale, f"legacy OLE2 tokens still advertised: {sorted(stale)}"


def test_capability_keys_are_uploadable_sources() -> None:
    view = conversion_capability()
    unuploadable = sorted(set(view) - set(ALLOWED_EXTENSIONS))
    assert not unuploadable, (
        f"rows for sources the validator rejects (dead by construction): {unuploadable}"
    )


def test_default_target_order_is_pinned() -> None:
    """Array order IS the auto-default policy (WS1: wav must not default to FLAC)."""

    view = conversion_capability()
    assert view["wav"][0] == "MP3", f"wav auto-default changed: {view['wav']}"
    assert view["mp3"][0] == "WAV", f"mp3 auto-default changed: {view['mp3']}"
    assert view["mp4"][0] == "AAC", f"mp4 auto-default changed: {view['mp4']}"
    assert set(view["wav"]) == {"MP3", "FLAC", "AAC"}


# ---------------------------------------------------------------------------
# 3. Self-conversion is operation context, never a plain conversion option.
# ---------------------------------------------------------------------------


def test_plain_conversion_view_has_no_self_conversions() -> None:
    """jpg->jpg (watermark), png->png / mp4->mp4 (compress), pdf->pdf (split) and
    the archive selves all live in the pair index. The homepage posts no
    ``operation``, so advertising any of them would silently run an operation the
    user never selected."""

    for source, targets in conversion_capability().items():
        assert source.upper() not in targets, (
            f"{source} advertises a self target in the conversion view"
        )


def test_extract_operations_advertise_exactly_their_own_pair() -> None:
    base = build_capability().map
    for slug, ext in EXTRACT_OPERATIONS.items():
        operation_view = build_capability(slug).map
        added = {
            source: sorted(set(targets) - set(base.get(source, [])))
            for source, targets in operation_view.items()
            if set(targets) - set(base.get(source, []))
        }
        assert added == {ext: [ext]}, (
            f"{slug}: operation overlay must add only {ext}->{ext}, got {added}"
        )


def test_operation_overlay_never_exceeds_the_d4_guard() -> None:
    """Everything an operation page offers must be a pair get_plugin(slug=...)
    accepts - the same authority that keeps a duplicate slug from advertising a
    shadowed class's claim (D4)."""

    guard = registry.slug_winner_pairs
    for slug in EXTRACT_OPERATIONS:
        offered = build_capability(slug).map
        for source, targets in offered.items():
            for target in targets:
                pair = (source, target.lower())
                in_conversion = pair in registry.plugins and source != target
                assert in_conversion or pair in guard.get(slug, set()), (
                    f"{slug}: {source}->{target} is offered but not authorized by "
                    "slug_winner_pairs nor by the pair index"
                )


# ---------------------------------------------------------------------------
# 4. Consumer 1: homepage must render the derived capability, not a literal.
# ---------------------------------------------------------------------------


def test_homepage_template_has_no_hand_maintained_literal() -> None:
    src = HOME_TEMPLATE.read_text(encoding="utf-8")
    assert "const STATIC_TARGET_MAP = {{" in src, (
        "homepage still declares its own target map instead of consuming the "
        "server-rendered capability"
    )
    assert "// image sources" not in src, (
        "the hand-maintained STATIC_TARGET_MAP literal is still in the template"
    )


def test_homepage_serves_the_authoritative_capability(client: TestClient) -> None:
    assert served_homepage_map(client) == conversion_capability()


def test_homepage_no_longer_offers_the_dead_pdf_to_word(client: TestClient) -> None:
    served = served_homepage_map(client)
    pdf_targets = served.get("pdf", [])
    assert "WORD" not in pdf_targets, "homepage still offers pdf -> WORD (placeholder)"
    assert "DOC" not in pdf_targets, "homepage still offers a non-delivered .doc target"
    assert "DOCX" in pdf_targets, "pdf -> DOCX is a real capability and must stay"


def test_homepage_bulk_options_come_from_the_capability_intersection() -> None:
    """The mixed-category bulk list used to be a hardcoded guess of
    ['JPG','PNG','PDF','MP3','MP4','ZIP'] - values that are not valid for the
    pending rows at all. It must now be derived, and can therefore never mention
    a format that no pending row can convert to."""

    src = HOME_TEMPLATE.read_text(encoding="utf-8")
    start = src.index("function buildGlobalFmt()")
    body = src[start:src.index("function conversionErrorMessage", start)]
    assert "'JPG','PNG','PDF','MP3','MP4','ZIP'" not in body.replace(
        "'JPG', 'PNG'", "'JPG','PNG'"
    ), "buildGlobalFmt() still seeds the bulk control from a hardcoded format list"
    assert body.count("getValidTargets(") >= 2, (
        "buildGlobalFmt() must derive its options from the capability map"
    )


# ---------------------------------------------------------------------------
# 5. Consumer 2: the tool-page widget must render the SAME derived source.
# ---------------------------------------------------------------------------

MOUNTED_OPERATIONS = ("tar-extract", "zip-extract", "gz-extract")


@pytest.fixture
def widget_enabled(monkeypatch):
    """Force the V2 widget on, exactly as tests/test_result_widget_wiring.py does."""

    import app.routers.tools as tools_router

    monkeypatch.setattr(tools_router, "is_result_widget_v2_enabled", lambda **kwargs: True)


def test_widget_js_has_no_hand_maintained_literal() -> None:
    src = WIDGET_JS.read_text(encoding="utf-8")
    assert "var STATIC_TARGET_MAP = {" not in src, (
        "tool_result_widget_v2.js still owns a copy of the capability map"
    )
    assert "targetMap" in src, (
        "the widget must read the server-injected map from its mount element"
    )
    assert "'JPG','PNG','PDF','MP3','MP4','ZIP'" not in src.replace(
        "'JPG', 'PNG'", "'JPG','PNG'"
    ), "widget bulk selector still falls back to a hardcoded format list"


@pytest.mark.parametrize("slug", MOUNTED_OPERATIONS)
def test_widget_mount_injects_the_capability(slug: str, client: TestClient, widget_enabled) -> None:
    served = served_widget_map(client, slug)
    expected = build_capability(slug).map
    expected = {s: [t.upper() for t in targets] for s, targets in expected.items()}
    assert served == expected, f"/tools/{slug}: injected map != derived capability"


@pytest.mark.parametrize("slug", MOUNTED_OPERATIONS)
def test_widget_and_homepage_share_one_source(slug: str, client: TestClient, widget_enabled) -> None:
    """The acceptance criterion for D5: one authoritative source feeding both
    consumers. The only permitted difference is the operation pair the mounted
    page itself is about (extract keeps its same-extension target)."""

    homepage = served_homepage_map(client)
    widget = served_widget_map(client, slug)
    ext = EXTRACT_OPERATIONS[slug]

    assert set(homepage) <= set(widget), "widget lost source rows the homepage has"
    for source, targets in homepage.items():
        if source == ext:
            continue  # the mounted page legitimately appends its own target
        assert widget[source] == targets, (
            f"{slug}: row {source} diverged from the homepage map: "
            f"{widget[source]} vs {targets}"
        )
    diff = {
        source: sorted(set(widget[source]) - set(homepage.get(source, [])))
        for source in widget
        if set(widget[source]) - set(homepage.get(source, []))
    }
    assert diff == {ext: [ext.upper()]}, (
        f"{slug}: widget may only add its own operation pair, got {diff}"
    )


# ---------------------------------------------------------------------------
# 6. The inert "Phase A matrix" authority must be gone.
# ---------------------------------------------------------------------------


def test_inert_phase_a_matrix_declaration_is_removed() -> None:
    """home.py loaded app/data/phase_a_matrix.json, warned when it was missing and
    passed it to the template - which never read it. Dead authority that only
    pretended to gate the UI; the live derived capability replaces it."""

    src = ROUTER_HOME.read_text(encoding="utf-8")
    assert "phase_a_matrix" not in src, "home.py still declares the inert matrix authority"
    assert not (REPO_ROOT / "app" / "data" / "phase_a_matrix.json").exists(), (
        "the snapshot file is not tracked in git and must not be recreated"
    )


# ---------------------------------------------------------------------------
# 7. Contract prose must agree with the authoritative capability.
# ---------------------------------------------------------------------------

CONTRACT_DIR = REPO_ROOT / "app" / "data" / "converters"
APPROVED_CONTRACT_PROSE = ("pdf-to-word", "word-to-pdf", "docx-to-ppt", "ppt-to-docx")


def _norm(token: str) -> str:
    return str(token).strip().lstrip(".").lower()


@pytest.mark.parametrize("slug", APPROVED_CONTRACT_PROSE)
def test_tool_page_prose_matches_registered_capability(slug: str) -> None:
    """A tool page that claims an input it cannot accept, or an output it never
    delivers, is the same class of lie as a dead dropdown entry - it just fails
    further downstream. Every advertised extension must be backed by the pairs
    the winning plugin for this slug actually claims."""

    data = json.loads((CONTRACT_DIR / f"{slug}.json").read_text(encoding="utf-8"))
    formats = data.get("supported_formats") or {}
    claimed_inputs = [_norm(x) for x in formats.get("input", [])]
    claimed_outputs = [_norm(x) for x in formats.get("output", [])]
    assert claimed_inputs and claimed_outputs, f"{slug}: no supported_formats block"

    authorized = registry.slug_winner_pairs.get(slug)
    assert authorized, f"{slug}: slug is not registered, so the page must not exist"

    contract = CONTRACT_DIR / f"{slug}.contract.json"
    if contract.exists():
        machine = json.loads(contract.read_text(encoding="utf-8"))
        claimed_inputs += [_norm(x) for x in machine.get("input_formats", [])]
        claimed_outputs += [_norm(x) for x in machine.get("output_formats", [])]

    for token in claimed_inputs:
        assert token in ALLOWED_EXTENSIONS, (
            f"{slug}: contract advertises input .{token}, which the upload "
            "validator rejects"
        )
        assert TARGET_CANONICAL.get(token, token) == token, (
            f"{slug}: contract advertises non-canonical input token {token}"
        )
        assert any(source == token for source, _ in authorized), (
            f"{slug}: input {token} is not a source the dispatched plugin accepts"
        )

    for token in claimed_outputs:
        assert TARGET_CANONICAL.get(token, token) == token, (
            f"{slug}: contract advertises {token} but the plugin delivers "
            f"{TARGET_CANONICAL.get(token, token)}"
        )
        assert any(target == token for _, target in authorized), (
            f"{slug}: output {token} is not a target the dispatched plugin claims"
        )


def test_word_to_pdf_accept_metadata_matches_pr1() -> None:
    """PR-1 disabled legacy .doc uploads honestly; the upload widget's accept
    string must not keep offering a file the validator will refuse."""

    data = json.loads((CONTRACT_DIR / "word-to-pdf.json").read_text(encoding="utf-8"))
    accept = {_norm(x) for x in (data.get("upload_form") or {}).get("accept", "").split(",") if x}
    assert accept, "word-to-pdf: upload_form.accept missing"
    assert "doc" not in accept, ".doc is refused by the validator (PR-1) but still accepted"
    assert accept <= set(ALLOWED_EXTENSIONS), f"accept lists unuploadable types: {accept}"
    assert accept == {source for source, _ in registry.slug_winner_pairs["word-to-pdf"]}


# ---------------------------------------------------------------------------
# 8. Bulk-selector intersection, folded in from the stale Playwright-only node
#    test_globalfmt_no_common_target_for_jpg_png (which asserted a frozen
#    "Phase A matrix" answer of {TIFF, WEBP} that the maps long ago outgrew).
# ---------------------------------------------------------------------------


def _intersection(view: dict[str, list[str]], *exts: str) -> set[str]:
    sets = [set(view.get(ext, [])) for ext in exts]
    return set.intersection(*sets) if sets else set()


def test_bulk_intersection_matches_capability() -> None:
    view = conversion_capability()

    # Two images that really do share converters: everything jpg can produce that
    # png can also produce.
    assert _intersection(view, "jpg", "png") == {"ICO", "PDF", "TIFF", "TXT", "WEBP"}

    # Cross-family batches have no honest common target, so the bulk control must
    # offer nothing rather than guessing (the old hardcoded fallback did guess).
    assert _intersection(view, "png", "m4a") == set()
    assert _intersection(view, "jpg", "mp4") == set()
    assert _intersection(view, "pdf", "mp3") == set()


def test_bulk_intersection_contains_no_unreachable_value() -> None:
    """Every value the bulk control can offer must be individually dispatchable,
    otherwise picking it turns one valid batch into N failing requests."""

    view = conversion_capability()
    keys = sorted(view)
    for i, first in enumerate(keys):
        for second in keys[i:]:
            for target in _intersection(view, first, second):
                assert (first, target.lower()) in registry.plugins
                assert (second, target.lower()) in registry.plugins
