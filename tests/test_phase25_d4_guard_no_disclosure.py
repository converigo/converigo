"""
Phase 25.x D4 regression suite.

Two defects are pinned here.

F2 - guard / dispatch reconciliation
    ``PluginRegistry.by_slug`` is a single-winner index (last registration of a
    slug wins) while ``PluginRegistry.registered_keys`` is the accumulated
    *union* of every (source, target) pair ever claimed by any class using that
    slug. Before the fix ``get_plugin(slug=...)`` validated the request against
    the union and then dispatched to the winner, so a pair that only a
    *shadowed* class claimed passed the guard and reached an instance that
    cannot serve it. The registry now guards against the winner's own claim set
    (``slug_winner_pairs``).

    Required outcome (interim behaviour approved by the Supervisor; the product
    decision on whether pdf -> word should work at all is deferred to Q1/Q2):
        pdf + word + operation=pdf-to-word  -> 422 UNSUPPORTED_CONVERSION
        pdf + word (no operation)           -> 422 UNSUPPORTED_CONVERSION
    The (word, pdf) ghost on ``word-to-pdf`` closes by the same mechanism.

F1 - no information disclosure
    ConversionService used to copy the plugin's internal exception text and the
    Python exception class name into ConversionError, and convert.py echoed that
    into the HTTPException detail (single file, 500) and into results[].error /
    results[].error_code (batch, 201). Failure responses are now the structured
    {"success": false, "code": "...", "message": "..."} contract with a stable
    public code that is never derived from a Python class name.

The disclosure sweep is deliberately general: it covers the RuntimeError
amplifier, the generic Exception amplifier and the timeout path for both the
single-file and the batch response, not just the pdf-to-word collision.
"""

from __future__ import annotations

import asyncio
import io
import json
import re
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry
from app.services.conversion_service import (
    ConversionError,
    ConversionService,
    UnsupportedConversionError,
)

ASSETS = Path("tests/assets/regression")
PDF_SAMPLE = ASSETS / "sample.pdf"

# Public error codes that are allowed to reach a client. Anything outside this
# set - most importantly a code derived from a Python class name such as
# "CONVERSIONERROR" / "UPLOADERROR" - is a regression.
ALLOWED_PUBLIC_ERROR_CODES = {
    "BATCH_CONVERSION_FAILED",
    "CONVERSION_FAILED",
    "CONVERSION_TIMEOUT",
    "INVALID_TARGETS",
    "INVALID_TARGETS_LENGTH",
    "NO_FILES_PROVIDED",
    "NO_TARGET_SPECIFIED",
    "UNSUPPORTED_CONVERSION",
    "UNSUPPORTED_FILE_TYPE",
    "UPLOAD_FAILED",
}

# Substrings that must never appear anywhere in a client response body.
_INTERNAL_MARKERS = (
    "Traceback",
    "PDFToWordPlugin",
    "WordToPDFPlugin",
    "_OfficePlaceholderPlugin",
    "DocumentEngine",
    "ConversionError",
    "UnsupportedConversionError",
    "UploadError",
    "UploadRejectedError",
    "RuntimeError",
    "ValueError",
    "KeyError",
    "TimeoutError",
    "site-packages",
    ".venv",
    "/app/",
    "uploads\\",
    "uploads/",
    "internal-canary",
)

# Structural patterns that expose internals even when the exact class name is
# not one of the markers above.
_PLUGIN_CLASS_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*Plugin\b")
_EXCEPTION_CLASS_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:Error|Exception)\b")
_MODULE_PATH_RE = re.compile(r"\b(?:app|tests)\.[A-Za-z_][A-Za-z0-9_.]*")
_FILE_PATH_RE = re.compile(r"(?:/app/|/var/|/tmp/|[A-Za-z]:\\\\|\.py\b|\.pyc\b)")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def assert_no_internal_leak(payload: object, label: str) -> None:
    """Fail if any internal implementation detail is present in a response."""
    text = json.dumps(payload)
    leaked = [marker for marker in _INTERNAL_MARKERS if marker.lower() in text.lower()]
    assert not leaked, f"{label}: internal detail leaked: {leaked} in {text[:600]!r}"

    for pattern, kind in (
        (_PLUGIN_CLASS_RE, "plugin class name"),
        (_EXCEPTION_CLASS_RE, "exception class name"),
        (_MODULE_PATH_RE, "module dotted path"),
        (_FILE_PATH_RE, "filesystem path"),
    ):
        hits = sorted(set(pattern.findall(text)))
        assert not hits, f"{label}: {kind} leaked: {hits} in {text[:600]!r}"


def assert_public_codes(payload: object, label: str) -> None:
    """Every code / error_code that reaches a client must be a public literal."""
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"code", "error_code"} and isinstance(value, str):
                    found.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    unknown = sorted({code for code in found if code not in ALLOWED_PUBLIC_ERROR_CODES})
    assert not unknown, f"{label}: non-public error code(s) {unknown} in {json.dumps(payload)[:600]}"


def ghost_pair_slugs() -> dict[str, set]:
    """Slugs whose accumulated claim set advertises pairs the winner can't serve."""
    ghosts: dict[str, set] = {}
    for slug, winner in registry.by_slug.items():
        declared = set(winner.registration_pairs())
        ghosts[slug] = set(registry.registered_keys.get(slug, [])) - declared
    return {slug: pairs for slug, pairs in ghosts.items() if pairs}


def post_convert(client: TestClient, files, data: dict):
    return client.post("/convert", files=files, data=data)


def pdf_files_list(count: int = 2) -> list:
    """Multiple uploads under the same `file` field (the batch path)."""
    payload = PDF_SAMPLE.read_bytes()
    return [("file", (f"batch-{i}.pdf", payload, "application/pdf")) for i in range(count)]


def download_bytes(download_path: str) -> bytes:
    """Read a /download/<conversion_id>/<file> result from disk, then clean up."""
    relative = download_path.removeprefix("/download/")
    output_path = settings.OUTPUT_DIR.joinpath(*Path(relative).parts)
    payload = output_path.read_bytes()
    output_path.unlink(missing_ok=True)
    return payload


def broken_plugin_convert(exc_factory):
    """An async convert() that always raises an internal-looking exception."""

    async def _convert(source_path, target_format, output_dir=None, temp_dir=None, **kwargs):
        raise exc_factory()

    return _convert


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture()
def pdf_files() -> dict:
    return {"file": (PDF_SAMPLE.name, PDF_SAMPLE.read_bytes(), "application/pdf")}



# ---------------------------------------------------------------------------
# 1. F2 - registry consistency invariant (highest priority)
# ---------------------------------------------------------------------------
def test_guard_authority_is_the_winner_declared_pairs() -> None:
    """For EVERY slug: the pairs the guard accepts == the winner's own pairs.

    This is the invariant that produced D4. The guard must never be wider than
    the instance by_slug actually dispatches to, otherwise a ghost pair reaches
    a plugin that rejects it at run time and the request becomes a 500.
    """
    offenders = []
    for slug, winner in registry.by_slug.items():
        declared = set(winner.registration_pairs())
        accepted = set(registry.slug_winner_pairs.get(slug, ()))
        if accepted != declared:
            offenders.append(f"{slug}: guard={sorted(accepted)} winner={sorted(declared)}")
    assert not offenders, "guard/dispatch divergence: " + "; ".join(offenders)


def test_registry_has_no_ghost_keys_left_unreconciled() -> None:
    """Every shadowed claim must be refused by the live guard, not just in an index.

    Behavior-level on purpose: it drives get_plugin() for each pair that only a
    shadowed class claimed, so a future duplicate slug cannot reintroduce a
    ghost key that reaches a plugin which rejects it at run time.
    """
    ghosts = ghost_pair_slugs()
    assert ghosts, "fixture drift: expected the known duplicate-slug ghosts to exist"
    still_accepted = []
    for slug, pairs in ghosts.items():
        for source, target in sorted(pairs):
            try:
                plugin = registry.get_plugin(source, target, slug=slug)
            except ValueError:
                continue
            still_accepted.append(f"{slug} {source}->{target} resolved to {type(plugin).__name__}")
    assert not still_accepted, "ghost keys still accepted by the guard: " + ", ".join(still_accepted)


def test_duplicate_slugs_still_diverge_in_the_union_index() -> None:
    """Why the invariant matters: these slugs have shadowed claimants.

    registered_keys keeps the union of every class that ever claimed the slug,
    so it stays wider than the winner for exactly the duplicate-slug cases.
    The guard must not read it any more.
    """
    ghosts = ghost_pair_slugs()
    assert ghosts.get("pdf-to-word") == {("pdf", "word")}, ghosts
    assert ghosts.get("word-to-pdf") == {("word", "pdf")}, ghosts


def test_ghost_pairs_are_rejected_by_the_guard() -> None:
    """The two ghost pairs must be refused at resolution time, not at run time."""
    with pytest.raises(ValueError):
        registry.get_plugin("pdf", "word", slug="pdf-to-word")
    with pytest.raises(ValueError):
        registry.get_plugin("word", "pdf", slug="word-to-pdf")


def test_declared_pairs_still_resolve_with_and_without_operation() -> None:
    """F2 narrows the guard to the winner; it must not break real lookups."""
    assert registry.get_plugin("pdf", "word").slug == "pdf-to-word"
    assert registry.get_plugin("word", "pdf").slug == "word-to-pdf"
    assert registry.get_plugin("pdf", "docx", slug="pdf-to-word") is registry.by_slug["pdf-to-word"]
    assert registry.get_plugin("pdf", "doc", slug="pdf-to-word") is registry.by_slug["pdf-to-word"]
    assert registry.get_plugin("docx", "pdf", slug="word-to-pdf") is registry.by_slug["word-to-pdf"]


def test_guard_rejection_becomes_an_honest_unsupported_error(tmp_path) -> None:
    """Service level: a ghost pair maps to UnsupportedConversionError, never a 500."""
    stub = tmp_path / "document.word"
    stub.write_bytes(b"not a real document")

    service = ConversionService()
    with pytest.raises(UnsupportedConversionError):
        asyncio.run(service.convert_file(stub, "pdf", plugin_slug="word-to-pdf"))


def test_guard_behaviour_is_unchanged_for_slugs_without_ghost_keys() -> None:
    """F2 must be a no-op for every non-colliding slug (the 115 others).

    For those slugs the accumulated union already equals the winner's own claim
    set, so no accept/reject decision can have moved.
    """
    ghosted = set(ghost_pair_slugs())
    checked = 0
    for slug, winner in registry.by_slug.items():
        if slug in ghosted:
            continue
        declared = set(winner.registration_pairs())
        assert set(registry.registered_keys.get(slug, [])) == declared, slug
        assert set(registry.slug_winner_pairs.get(slug, ())) == declared, slug
        for source, target in declared:
            assert registry.get_plugin(source, target, slug=slug) is winner, f"{slug} {source}->{target}"
            checked += 1
        with pytest.raises(ValueError):
            registry.get_plugin("nope", "nothing", slug=slug)
    assert len(registry.by_slug) > 100, "expected the full plugin catalogue to be registered"
    assert checked > 100, "non-colliding spot-check degenerated to nothing"



# ---------------------------------------------------------------------------
# 2. F2 - required HTTP outcome: honest-unavailable, identically with and
#    without the operation slug
# ---------------------------------------------------------------------------
def _assert_honest_422(response, label: str) -> dict:
    assert response.status_code == 422, f"{label}: {response.status_code} {response.text[:400]}"
    body = response.json()
    assert body.get("success") is False, f"{label}: {body}"
    assert body.get("code") == "UNSUPPORTED_CONVERSION", f"{label}: {body}"
    assert isinstance(body.get("message"), str) and body["message"], f"{label}: {body}"
    assert "download_path" not in json.dumps(body), f"{label}: advertised a download: {body}"
    assert_no_internal_leak(body, label)
    assert_public_codes(body, label)
    return body


def test_pdf_to_word_with_operation_returns_honest_422(client, pdf_files) -> None:
    _assert_honest_422(
        post_convert(client, pdf_files, {"target_format": "word", "operation": "pdf-to-word"}),
        "pdf + word + operation=pdf-to-word",
    )


def test_pdf_to_word_without_operation_returns_honest_422(client, pdf_files) -> None:
    _assert_honest_422(
        post_convert(client, pdf_files, {"target_format": "word"}),
        "pdf + word, no operation",
    )


def test_both_collision_paths_share_one_response_shape(client, pdf_files) -> None:
    """With and without the slug must answer through the same mechanism."""
    with_operation = _assert_honest_422(
        post_convert(client, pdf_files, {"target_format": "word", "operation": "pdf-to-word"}),
        "with operation",
    )
    without_operation = _assert_honest_422(
        post_convert(client, pdf_files, {"target_format": "word"}),
        "without operation",
    )
    shared = {"success", "code", "message", "request_id", "conversion_id"}
    assert set(with_operation) == shared, with_operation
    assert set(without_operation) == shared, without_operation
    assert with_operation["code"] == without_operation["code"]


def test_word_to_pdf_ghost_is_closed_the_same_way() -> None:
    """(word, pdf) is only reachable by bypassing the upload allow-list (Q4),
    so the closure is asserted at the guard rather than over HTTP."""
    with pytest.raises(ValueError):
        registry.get_plugin("word", "pdf", slug="word-to-pdf")
    assert ("word", "pdf") not in registry.slug_winner_pairs["word-to-pdf"]


# ---------------------------------------------------------------------------
# 3. F1 - disclosure sweep: single-file and batch
# ---------------------------------------------------------------------------
def _failure_sweep_cases() -> list[tuple[str, dict, int, int]]:
    """(label, form data, single-file status, batch status)

    Batch answers 201 with per-item failures; an unregistered slug is rejected
    pre-flight for any file count, so it stays a 422 even on the batch path.
    """
    return [
        ("ghost-pair-with-operation", {"target_format": "word", "operation": "pdf-to-word"}, 422, 201),
        ("ghost-pair-no-operation", {"target_format": "word"}, 422, 201),
        ("slug-target-mismatch", {"target_format": "xlsx", "operation": "pdf-to-word"}, 422, 201),
        ("slug-source-mismatch", {"target_format": "pdf", "operation": "word-to-pdf"}, 422, 201),
        ("unknown-slug", {"target_format": "docx", "operation": "definitely-not-a-slug"}, 422, 422),
        ("unknown-target", {"target_format": "zzz"}, 422, 201),
    ]


@pytest.mark.parametrize("label,data,expected,batch_expected", _failure_sweep_cases())
def test_single_file_failure_responses_disclose_nothing(client, pdf_files, label, data, expected, batch_expected) -> None:
    response = post_convert(client, pdf_files, data)
    assert response.status_code == expected, f"{label}: {response.status_code} {response.text[:400]}"
    assert_no_internal_leak(response.json(), f"single-file {label}")
    assert_public_codes(response.json(), f"single-file {label}")


@pytest.mark.parametrize("label,data,expected,batch_expected", _failure_sweep_cases())
def test_batch_failure_responses_disclose_nothing(client, label, data, expected, batch_expected) -> None:
    response = post_convert(client, pdf_files_list(2), data)
    # The outer batch contract (HTTP 201 + per-item status) is deliberately
    # unchanged: only the content of the per-item error fields is sanitized.
    assert response.status_code == batch_expected, f"{label}: {response.status_code} {response.text[:400]}"
    body = response.json()
    if batch_expected != 201:
        assert_no_internal_leak(body, f"batch-pre-flight {label}")
        assert_public_codes(body, f"batch-pre-flight {label}")
        return
    assert {"status", "conversion_id", "results", "total", "successful"} <= set(body), body
    assert body["total"] == 2 and len(body["results"]) == 2, body
    for item in body["results"]:
        assert item["status"] == "failed", item
        assert item.get("error"), item
    assert_no_internal_leak(body, f"batch {label}")
    assert_public_codes(body, f"batch {label}")


def test_upload_policy_rejection_stays_415_and_discloses_nothing(client) -> None:
    """The PR-1 415 channel keeps its guidance text but must not leak internals."""
    ole2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 504
    response = post_convert(
        client,
        {"file": ("legacy.xls", ole2, "application/vnd.ms-excel")},
        {"target_format": "pdf", "operation": "excel-to-pdf"},
    )
    assert response.status_code == 415, response.text[:400]
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_FILE_TYPE", body
    assert_no_internal_leak(body, "upload rejection")
    assert_public_codes(body, "upload rejection")



# ---------------------------------------------------------------------------
# 4. F1 - the two amplifier sites, plus the timeout path
# ---------------------------------------------------------------------------
def test_service_does_not_amplify_plugin_runtime_error(tmp_path) -> None:
    """Unit level: ConversionError must not carry the plugin's internal text."""
def test_service_does_not_amplify_plugin_runtime_error(tmp_path, monkeypatch) -> None:
    """Unit level: ConversionError must not carry the plugin's internal text."""
    source = tmp_path / "input.pdf"
    source.write_bytes(PDF_SAMPLE.read_bytes())

    monkeypatch.setattr(
        registry.by_slug["pdf-to-word"],
        "convert",
        broken_plugin_convert(
            lambda: RuntimeError("PDFToWordPlugin only supports PDF -> DOCX/DOC.")
        ),
    )

    with pytest.raises(ConversionError) as excinfo:
        asyncio.run(ConversionService().convert_file(source, "docx"))

    assert "PDFToWordPlugin" not in str(excinfo.value)
    assert "RuntimeError" not in str(excinfo.value)



def test_runtime_error_amplifier_is_not_echoed(client, pdf_files, monkeypatch) -> None:
    """The production D4 message text must never reach a client again."""
    monkeypatch.setattr(
        registry.by_slug["pdf-to-word"],
        "convert",
        broken_plugin_convert(
            lambda: RuntimeError("PDFToWordPlugin only supports PDF -> DOCX/DOC.")
        ),
    )

    response = post_convert(client, pdf_files, {"target_format": "docx", "operation": "pdf-to-word"})
    assert response.status_code == 500, response.text[:400]
    body = response.json()
    assert body.get("success") is False, body
    assert body.get("code") == "CONVERSION_FAILED", body
    assert isinstance(body.get("message"), str) and body["message"], body
    assert "detail" not in body, f"raw string detail returned: {body}"
    assert_no_internal_leak(body, "runtime-error amplifier")
    assert_public_codes(body, "runtime-error amplifier")


def test_generic_exception_amplifier_is_not_echoed(client, pdf_files, monkeypatch) -> None:
    monkeypatch.setattr(
        registry.by_slug["pdf-to-word"],
        "convert",
        broken_plugin_convert(
            lambda: KeyError("internal-canary failure in /app/plugins/document/pdf_to_word.py")
        ),
    )

    response = post_convert(client, pdf_files, {"target_format": "docx", "operation": "pdf-to-word"})
    assert response.status_code == 500, response.text[:400]
    body = response.json()
    assert body.get("code") == "CONVERSION_FAILED", body
    assert_no_internal_leak(body, "generic-exception amplifier")
    assert_public_codes(body, "generic-exception amplifier")


def test_timeout_keeps_its_own_code_without_leaking(client, pdf_files, monkeypatch) -> None:
    """Timed-out conversions stay distinguishable by code, never by internals."""
    monkeypatch.setattr(settings, "DOCUMENT_CONVERSION_TIMEOUT_SECONDS", 1, raising=False)

    async def _slow(source_path, target_format, output_dir=None, temp_dir=None, **kwargs):
        await asyncio.sleep(5)

    monkeypatch.setattr(registry.by_slug["pdf-to-word"], "convert", _slow)

    response = post_convert(client, pdf_files, {"target_format": "docx", "operation": "pdf-to-word"})
    assert response.status_code == 500, response.text[:400]
    body = response.json()
    assert body.get("code") == "CONVERSION_TIMEOUT", body
    assert_no_internal_leak(body, "timeout amplifier")
    assert_public_codes(body, "timeout amplifier")


def test_batch_amplifier_results_are_sanitized(client, monkeypatch) -> None:
    monkeypatch.setattr(
        registry.by_slug["pdf-to-word"],
        "convert",
        broken_plugin_convert(
            lambda: RuntimeError("PDFToWordPlugin only supports PDF -> DOCX/DOC.")
        ),
    )
    response = post_convert(client, pdf_files_list(2), {"target_format": "docx", "operation": "pdf-to-word"})
    assert response.status_code == 201, response.text[:400]
    body = response.json()
    assert body["successful"] == 0, body
    assert len(body["results"]) == 2, body
    for item in body["results"]:
        assert item["status"] == "failed", item
        assert item["error_code"] == "CONVERSION_FAILED", item
        assert item["error"] == body["results"][0]["error"], item
    assert_no_internal_leak(body, "batch amplifier")
    assert_public_codes(body, "batch amplifier")


# ---------------------------------------------------------------------------
# 5. valid paths must be untouched by F1 + F2
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("target,operation", [("docx", "pdf-to-word"), ("docx", None), ("doc", "pdf-to-word"), ("doc", None)])
def test_pdf_to_word_valid_paths_still_produce_genuine_ooxml(client, pdf_files, target, operation) -> None:
    data = {"target_format": target}
    if operation:
        data["operation"] = operation

    response = post_convert(client, pdf_files, data)
    assert response.status_code == 201, f"{target}/{operation}: {response.status_code} {response.text[:400]}"
    body = response.json()
    assert body["status"] == "success", body
    assert body["filename"].endswith(".docx"), body

    payload = download_bytes(body["download_path"])
    assert payload[:2] == b"PK", "output is not a ZIP container"
    names = zipfile.ZipFile(io.BytesIO(payload)).namelist()
    assert "word/document.xml" in names, names


def test_word_to_pdf_declared_pair_still_works(client) -> None:
    """The collision winner keeps serving the pair it genuinely declares."""
    docx = ASSETS / "sample.docx"
    response = post_convert(
        client,
        {"file": (docx.name, docx.read_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        {"target_format": "pdf", "operation": "word-to-pdf"},
    )
    assert response.status_code == 201, response.text[:400]
    body = response.json()
    assert body["status"] == "success", body
    assert body["download_path"].endswith(".pdf"), body
    assert download_bytes(body["download_path"])[:5] == b"%PDF-"


