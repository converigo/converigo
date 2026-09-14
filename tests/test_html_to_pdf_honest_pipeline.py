"""
Acceptance tests for the html-to-pdf pipeline.

These are not unit tests of helper functions; every test asserts an externally
visible promise of the feature:

* limits are enforced *before* a render child exists, so a pathological
  document can never cost a process spawn,
* the blocking render never runs on the event loop,
* a hung / crashed / lying child is contained and the next conversion works,
* a refused document leaves no servable file,
* the client sees a static, honest message - never a path, exit code, signal
  number, library name or traceback,
* the landing page promises exactly the limits the code enforces,
* the committed calibration evidence still matches the constants in use.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from app.factory import html_pdf_runner as runner
from app.plugins.document.html_to_pdf import HTMLToPDFPlugin
from app.services.conversion_service import UnsupportedConversionError

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "html_to_pdf"
CONVERTERS = REPO_ROOT / "app" / "data" / "converters"

# Anything that would tell a caller about our internals.  Checked against
# client-facing text only; server-side detail is allowed (and meant) to carry it.
FORBIDDEN_CLIENT_TOKENS = (
    "Traceback",
    ".py",
    "exit=",
    "status=",
    "signal",
    "stderr",
    "child",
    "MuPDF",
    "fitz",
    "CONVERIGO_HTML_RENDER_RESULT",
    "utf-8",
    "byte",
    "\\",
    "/",
    "C:",
    "temp",
)


def fixture_path(name: str) -> Path:
    path = FIXTURES / name
    assert path.is_file(), f"committed fixture {name} is missing"
    return path


def write_case(tmp_path: Path, name: str, payload: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(payload)
    return path


@pytest.fixture()
def no_spawn(monkeypatch):
    """Record (and veto) any attempt to launch the render child."""
    calls: list[tuple] = []

    def _refuse(*args, **kwargs):  # pragma: no cover - must never run
        calls.append((args, kwargs))
        raise AssertionError("render child must not be spawned for this document")

    monkeypatch.setattr(runner.subprocess, "run", _refuse)
    return calls


@pytest.fixture(scope="module")
def sample_pdf_bytes(tmp_path_factory) -> bytes:
    """A genuine one-page PDF produced by the real child, reused by stubs."""
    output = tmp_path_factory.mktemp("htmlpdf-sample") / "sample.pdf"
    runner.render_html_document(fixture_path("valid_utf8.html"), output)
    return output.read_bytes()


# ---------------------------------------------------------------------------
# Stage 1 - intake limits are enforced before any process exists
# ---------------------------------------------------------------------------


def intake_case(tmp_path: Path, case: str) -> Path:
    """One source document per pre-render rejection reason."""
    limit = runner.MAX_HTML_INPUT_BYTES
    if case == "oversize":
        return write_case(tmp_path, "big.html", b"<p>" + b"x" * (limit + 8) + b"</p>")
    if case == "depth":
        depth = runner.MAX_ELEMENT_DEPTH + 100
        return write_case(
            tmp_path,
            "deep.html",
            ("<div>" * depth + "text" + "</div>" * depth).encode("utf-8"),
        )
    if case == "token":
        token = "z" * (runner.MAX_TOKEN_LENGTH + 1)
        return write_case(tmp_path, "token.html", f"<p>{token}</p>".encode())
    if case == "empty":
        return write_case(tmp_path, "empty.html", b"")
    if case == "invalid_utf8":
        return write_case(tmp_path, "bad.html", b"<p>bad \x80\x81 bytes</p>")
    if case == "cp1252_declared":
        text = (
            '<html><head><meta charset="windows-1252"></head>'
            "<body><p>Caf\xe9 r\xe9sum\xe9</p></body></html>"
        )
        return write_case(tmp_path, "cp1252.html", text.encode("cp1252"))
    raise AssertionError(f"unknown intake case {case}")


@pytest.mark.parametrize(
    ("case", "error"),
    [
        ("oversize", runner.HtmlInputTooLarge),
        ("depth", runner.HtmlStructureRejected),
        ("token", runner.HtmlStructureRejected),
        ("empty", runner.HtmlInputEmpty),
        ("invalid_utf8", runner.HtmlEncodingUnsupported),
        ("cp1252_declared", runner.HtmlEncodingUnsupported),
    ],
)
def test_rejected_before_the_render_child_exists(tmp_path, no_spawn, case, error):
    """A guard refusal must cost zero processes, not a killed child."""
    source = intake_case(tmp_path, case)

    with pytest.raises(error) as excinfo:
        runner.render_html_document(source, tmp_path / "out.pdf")

    assert no_spawn == []
    assert excinfo.value.detail
    # str(exc) is the static client text; the diagnostic stays an attribute.
    assert str(excinfo.value) == excinfo.value.client_message


def test_declared_charset_does_not_license_a_lossy_decode(tmp_path, no_spawn):
    """<meta charset> must not turn a refusal into silent mojibake.

    MuPDF does not honour the declaration either, so honouring it in intake
    would render text the user never wrote.
    """
    source = intake_case(tmp_path, "cp1252_declared")

    with pytest.raises(runner.HtmlEncodingUnsupported):
        runner.prepare_html_source(source)

    assert no_spawn == []


def test_utf8_and_bom_variants_are_accepted(tmp_path):
    for name in ("valid_utf8.html", "utf8_bom.html", "utf16_le_bom.html"):
        text = runner.prepare_html_source(fixture_path(name))
        assert text.strip()
        assert "\ufffd" not in text  # decoded, never replaced


def test_plugin_maps_every_intake_refusal_to_the_honest_422(tmp_path):
    source = intake_case(tmp_path, "oversize")

    with pytest.raises(UnsupportedConversionError) as excinfo:
        asyncio.run(
            HTMLToPDFPlugin().convert(source, "pdf", temp_dir=tmp_path / "work")
        )

    assert str(excinfo.value) == runner.HtmlInputTooLarge.client_message
    assert excinfo.value.source_format == "html"
    assert excinfo.value.target_format == "pdf"


# ---------------------------------------------------------------------------
# Stage 2 - the child process contract
# ---------------------------------------------------------------------------


def fake_run(
    monkeypatch,
    *,
    returncode: int = 0,
    report: dict | None = None,
    payload: bytes | None = None,
    delay: float = 0.0,
    stderr: str = "",
) -> list[dict]:
    """Replace the child with a controllable stand-in; record each invocation."""
    calls: list[dict] = []

    def _run(command, *args, **kwargs):
        calls.append({"command": list(command), "kwargs": kwargs})
        if delay:
            time.sleep(delay)
        target = Path(list(command)[list(command).index("--output") + 1])
        target.parent.mkdir(parents=True, exist_ok=True)
        if payload is not None:
            target.write_bytes(payload)
        stdout = ""
        if report is not None:
            stdout = f"{runner.RESULT_MARKER} {json.dumps(report)}\n"
        return subprocess.CompletedProcess(list(command), returncode, stdout, stderr)

    monkeypatch.setattr(runner.subprocess, "run", _run)
    return calls


def ok_report(payload: bytes) -> dict:
    return {"status": "ok", "pages": 1, "bytes": len(payload), "pid": 4242}


def test_html_crosses_to_the_child_on_stdin_not_the_command_line(
    tmp_path, monkeypatch, sample_pdf_bytes
):
    """A 500 KB document must never become an argv blob or a temp side file."""
    payload = sample_pdf_bytes
    calls = fake_run(monkeypatch, report=ok_report(payload), payload=payload)

    runner.render_html_document(fixture_path("valid_utf8.html"), tmp_path / "out.pdf")

    command = calls[0]["command"]
    assert Path(command[0]) == Path(sys.executable)
    assert Path(command[1]) == runner.RENDER_WORKER_PATH
    assert "--max-pages" in command
    joined = " ".join(command)
    assert "Converigo" not in joined  # the document body is not in argv
    assert "<p>" not in joined
    assert calls[0]["kwargs"]["input"].startswith("<")  # arrives on stdin


def test_worker_is_not_a_plugin_so_discovery_cannot_import_it():
    """app/plugins is rglob'd at start-up; the child must live outside it."""
    assert "plugins" not in runner.RENDER_WORKER_PATH.parts
    assert runner.RENDER_WORKER_PATH.name == "html_render_worker.py"


def test_render_work_runs_off_the_event_loop(tmp_path, monkeypatch, sample_pdf_bytes):
    """The whole point of to_thread: a slow child must not stall the loop.

    A 1 s child with the loop free should allow ~100 ticker rounds at 10 ms.
    A synchronous subprocess call inside convert() would yield 0-1, because the
    loop cannot run anything else while the coroutine blocks.
    """
    payload = sample_pdf_bytes
    fake_run(monkeypatch, report=ok_report(payload), payload=payload, delay=1.0)
    source = fixture_path("valid_utf8.html")
    plugin = HTMLToPDFPlugin()

    ticks = 0

    async def ticker():
        nonlocal ticks
        while True:
            await asyncio.sleep(0.01)
            ticks += 1

    async def scenario():
        conversion = asyncio.create_task(plugin.convert(source, "pdf", temp_dir=tmp_path))
        heartbeat = asyncio.create_task(ticker())
        started = time.perf_counter()
        result = await conversion
        await asyncio.sleep(0.05)
        heartbeat.cancel()
        return result, time.perf_counter() - started

    result, elapsed = asyncio.run(scenario())

    assert result.is_file() and result.read_bytes().startswith(b"%PDF-")
    assert elapsed >= 0.9
    assert ticks >= 30, f"event loop was blocked: only {ticks} ticks in {elapsed:.2f}s"


def stub_worker(tmp_path: Path, body: str) -> Path:
    """A real child process with scripted, deliberately bad behaviour."""
    path = tmp_path / "stub_worker.py"
    path.write_text(
        "import argparse, os, sys, time\n"
        "p = argparse.ArgumentParser()\n"
        'p.add_argument("--output", required=True)\n'
        'p.add_argument("--max-pages", type=int, default=500)\n'
        'p.add_argument("--page-size", default="a4")\n'
        'p.add_argument("--min-output-bytes", type=int, default=1)\n'
        "args = p.parse_args()\n"
        "sys.stdin.read()\n"
        + body
        + "\n",
        encoding="utf-8",
    )
    return path


def test_hung_child_is_stopped_and_its_partial_pdf_is_discarded(tmp_path, monkeypatch):
    """Real child, real hang, real kill - and no half-written file left behind."""
    monkeypatch.setattr(
        runner,
        "RENDER_WORKER_PATH",
        stub_worker(
            tmp_path,
            'open(args.output, "wb").write(b"%PDF-1.4 written then abandoned")\n'
            "time.sleep(30)",
        ),
    )
    output = tmp_path / "out.pdf"

    started = time.perf_counter()
    with pytest.raises(runner.HtmlRenderTimeout) as excinfo:
        runner.render_html_to_pdf("<p>slow document</p>", output, timeout_seconds=1)
    elapsed = time.perf_counter() - started

    assert elapsed < 10, f"timeout did not bound the child: {elapsed:.1f}s"
    assert not output.exists()
    assert str(excinfo.value) == runner.HtmlRenderTimeout.client_message


def test_crashed_child_is_contained_and_the_next_conversion_works(tmp_path, monkeypatch):
    """A child that dies mid-flight must not take the worker pool with it."""
    monkeypatch.setattr(
        runner, "RENDER_WORKER_PATH", stub_worker(tmp_path, "os._exit(143)")
    )

    with pytest.raises(runner.HtmlRenderCrashed) as excinfo:
        runner.render_html_to_pdf(
            "<p>crash me</p>", tmp_path / "out.pdf", timeout_seconds=10
        )

    assert "143" in excinfo.value.detail  # server-side
    assert "143" not in excinfo.value.client_message  # client-side

    monkeypatch.undo()
    served = tmp_path / "next.pdf"
    runner.render_html_document(fixture_path("valid_utf8.html"), served)
    assert served.read_bytes().startswith(b"%PDF-")


@pytest.mark.parametrize("returncode", [-11, -9, 137, 0xC0000005])
def test_signal_and_access_violation_deaths_read_as_crashes(
    tmp_path, monkeypatch, returncode
):
    """Exit codes are translated, never forwarded."""
    calls = fake_run(monkeypatch, returncode=returncode, report=None)

    with pytest.raises(runner.HtmlRenderCrashed) as excinfo:
        runner.render_html_document(
            fixture_path("valid_utf8.html"), tmp_path / "out.pdf"
        )

    assert calls and not (tmp_path / "out.pdf").exists()
    assert str(returncode) not in excinfo.value.client_message


def test_child_that_exits_zero_without_a_report_is_a_crash(tmp_path, monkeypatch):
    fake_run(monkeypatch, returncode=0, report=None)

    with pytest.raises(runner.HtmlRenderCrashed):
        runner.render_html_document(fixture_path("valid_utf8.html"), tmp_path / "out.pdf")


@pytest.mark.parametrize(
    ("status", "returncode", "error"),
    [
        ("render_failed", 3, runner.HtmlRenderFailed),
        ("page_limit", 4, runner.HtmlPageLimitExceeded),
        ("output_rejected", 5, runner.HtmlOutputInvalid),
        ("input_rejected", 2, runner.HtmlInputRejected),
    ],
)
def test_each_child_status_maps_to_its_own_error(tmp_path, monkeypatch, status, returncode, error):
    fake_run(
        monkeypatch,
        returncode=returncode,
        report={"status": status, "detail": "RenderError: layout failed", "pages": -1},
    )

    with pytest.raises(error) as excinfo:
        runner.render_html_document(fixture_path("valid_utf8.html"), tmp_path / "out.pdf")

    assert "RenderError" not in excinfo.value.client_message


def test_engine_missing_is_an_operator_error_not_a_user_422(tmp_path, monkeypatch):
    """No MuPDF on the box is our fault; it must not look like bad input."""
    fake_run(
        monkeypatch,
        returncode=6,
        report={"status": "engine_missing", "detail": "ImportError", "pages": -1},
    )

    with pytest.raises(RuntimeError) as excinfo:
        runner.render_html_document(fixture_path("valid_utf8.html"), tmp_path / "out.pdf")

    assert isinstance(excinfo.value, runner.HtmlRenderError) is False
    assert "engine" in str(excinfo.value).lower()


def test_child_stderr_and_paths_never_reach_the_client(tmp_path, monkeypatch):
    noise = (
        f"Traceback (most recent call last):\n"
        f'  File "{runner.RENDER_WORKER_PATH}", line 9, in main\n'
        "    fitz.Document=storyplace(page_size)\n"
        "MuPDF error: syntax: cannot open XPS document\n"
        f"cwd={REPO_ROOT} temp={tmp_path}\n"
    )
    fake_run(monkeypatch, returncode=3, report={"status": "render_failed", "detail": "x"}, stderr=noise)

    with pytest.raises(runner.HtmlRenderFailed) as excinfo:
        runner.render_html_document(fixture_path("valid_utf8.html"), tmp_path / "out.pdf")

    message = excinfo.value.client_message
    for token in FORBIDDEN_CLIENT_TOKENS:
        assert token not in message, f"client message leaks {token!r}"
    assert str(excinfo.value) == message


# ---------------------------------------------------------------------------
# Stage 3 - the produced file is validated before anything is served
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "build"),
    [
        ("zero_byte", lambda sample: b""),
        ("not_a_pdf_at_all", lambda sample: b"Hello, I am definitely not a PDF."),
        ("header_without_trailer", lambda sample: b"%PDF-1.4 but nothing else"),
        ("truncated_tail", lambda sample: sample[:-400]),
    ],
)
def test_bad_pdf_bytes_are_refused_and_deleted(
    tmp_path, monkeypatch, sample_pdf_bytes, name, build
):
    fake_run(
        monkeypatch,
        report={"status": "ok", "pages": 1, "bytes": 1, "pid": 7},
        payload=build(sample_pdf_bytes),
    )
    output = tmp_path / "out.pdf"

    with pytest.raises(runner.HtmlOutputInvalid) as excinfo:
        runner.render_html_document(fixture_path("valid_utf8.html"), output)

    assert not output.exists(), f"{name}: refused bytes were left on disk"
    assert str(excinfo.value) == runner.HtmlOutputInvalid.client_message


@pytest.mark.parametrize("pages", [0, 501, -1])
def test_child_page_claims_are_not_trusted(
    tmp_path, monkeypatch, sample_pdf_bytes, pages
):
    fake_run(
        monkeypatch,
        report={
            "status": "ok",
            "pages": pages,
            "bytes": len(sample_pdf_bytes),
            "pid": 7,
        },
        payload=sample_pdf_bytes,
    )

    with pytest.raises(runner.HtmlOutputInvalid):
        runner.render_html_document(fixture_path("valid_utf8.html"), tmp_path / "out.pdf")


@pytest.mark.parametrize(
    "name",
    [
        "blank.html",
        "whitespace_only.html",
        "nbsp_only.html",
        "tiny_font.html",
        "white_on_white.html",
        "hidden_display_none.html",
        "script_generated_body.html",
    ],
)
def test_documents_that_would_show_nothing_are_not_served(tmp_path, name):
    """The seven empty fixtures all cost a real render, and all get refused."""
    output = tmp_path / "out.pdf"

    with pytest.raises(runner.HtmlOutputVisuallyEmpty) as excinfo:
        runner.render_html_document(fixture_path(name), output)

    assert not output.exists()
    assert str(excinfo.value) == runner.HtmlOutputVisuallyEmpty.client_message


def test_page_cap_is_enforced_by_the_child_itself(tmp_path):
    """5000 forced breaks must stop at 500, before a giant PDF is built."""
    output = tmp_path / "out.pdf"

    started = time.perf_counter()
    with pytest.raises(runner.HtmlPageLimitExceeded):
        runner.render_html_document(fixture_path("page_break_flood_5000.html"), output)

    assert time.perf_counter() - started < 15
    assert not output.exists()


def test_a_blank_tail_page_does_not_condemn_the_document(tmp_path):
    """Total ink, not per-page ink: a trailing empty page is normal pagination.

    A per-page rule would refuse this valid document, which is exactly the
    over-rejection MuPDF's own pagination makes common.
    """
    output = tmp_path / "out.pdf"

    outcome, report = runner.render_html_document(
        fixture_path("page_break_blank_tail.html"), output
    )

    assert report.pages == 2
    assert outcome.unresolved_images == 0
    assert report.ink_pixels >= runner.MIN_TOTAL_INK_PIXELS


def test_validation_stops_rasterizing_once_the_floor_is_cleared(tmp_path):
    """Page 1 answers the question; only inconclusive documents pay for more."""
    import fitz

    output = tmp_path / "out.pdf"
    runner.render_html_document(fixture_path("multipage_report.html"), output)

    with fitz.open(str(output)) as document:
        page_count = document.page_count
    report = runner.validate_html_output_pdf(output)

    assert page_count == 25  # per CALIBRATION.md
    assert report.pages == page_count
    assert report.pages_checked == 1
    assert report.early_exit is True


def test_ink_floor_matches_the_measured_blankness_of_real_documents():
    """Empty documents measured 0 ink; the smallest real mark measured 3.

    The floor sits between those two observations, so it is a measurement, not
    a round number (see tests/fixtures/html_to_pdf/CALIBRATION.md).
    """
    assert runner.MIN_TOTAL_INK_PIXELS == 1


def test_served_document_keeps_a_selectable_text_layer(tmp_path):
    import fitz

    served = asyncio.run(
        HTMLToPDFPlugin().convert(
            fixture_path("valid_report.html"), "pdf", temp_dir=tmp_path
        )
    )

    assert served.name == "valid_report.pdf"
    assert served.read_bytes().startswith(b"%PDF-")

    with fitz.open(str(served)) as document:
        assert document.page_count == 2  # per CALIBRATION.md
        text = "".join(document[index].get_text() for index in range(document.page_count))

    assert text.strip()  # a real text layer, not a rasterised page


def test_placeholder_text_in_prose_is_not_a_rejection_signal(tmp_path):
    """`[image]` is also legitimate writing, so it must never refuse a document.

    The honest observability metric counts unresolved <img> tags in the source,
    which is reported in logs but never gates delivery.
    """
    source = write_case(
        tmp_path,
        "prose.html",
        f"<p>The literal {runner.IMAGE_PLACEHOLDER_TOKEN} token is part of this "
        "sentence about placeholders.</p>".encode(),
    )

    outcome, report = runner.render_html_document(source, tmp_path / "out.pdf")

    assert outcome.unresolved_images == 0
    assert report.pages == 1
    assert runner.count_unresolved_image_tags(
        fixture_path("external_image_only.html").read_text(encoding="utf-8")
    ) == 2
    assert runner.count_unresolved_image_tags(
        fixture_path("data_uri_image.html").read_text(encoding="utf-8")
    ) == 0


# ---------------------------------------------------------------------------
# Honesty - the copy must promise exactly what the code enforces
# ---------------------------------------------------------------------------


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_contract_limits_are_the_runner_constants():
    contract = load_json(CONVERTERS / "html-to-pdf.contract.json")

    assert contract["max_upload_size"] == runner.MAX_HTML_INPUT_BYTES
    assert contract["input_formats"] == ["html"]  # .htm/.xhtml are NOT claimed
    assert contract["output_formats"] == ["pdf"]
    assert contract["conversion_engine"] == "document"
    assert (REPO_ROOT / contract["regression_sample"]).is_file()


def test_landing_page_discloses_the_measured_limitations():
    landing = load_json(CONVERTERS / "html-to-pdf.json")
    assert landing["slug"] == "html-to-pdf"
    assert landing["upload_form"]["accept"] == ".html"

    copy = json.dumps(landing)
    for promise in (
        "500 KB",  # MAX_HTML_INPUT_BYTES
        "500 pages",  # MAX_RENDER_PAGES
        "20 seconds",  # RENDER_TIMEOUT_SECONDS
        "UTF-8",  # strict intake decode
    ):
        assert promise in copy, f"landing page omits the enforced limit {promise!r}"

    for limitation in ("JavaScript", "data URI", "flexbox", "grid"):
        assert limitation in copy, f"landing page hides the limitation {limitation!r}"


def test_landing_page_does_not_overclaim_a_browser():
    copy = json.dumps(load_json(CONVERTERS / "html-to-pdf.json")).lower()

    for claim in (
        "pixel-perfect",
        "every website",
        "all css",
        "renders exactly like",
        "no size limit",
        "infinite pages",
    ):
        assert claim not in copy, f"landing page makes the false claim {claim!r}"


def test_calibration_evidence_still_matches_the_shipped_constants():
    """The committed evidence is only trustworthy if it describes this code."""
    text = (FIXTURES / "CALIBRATION.md").read_text(encoding="utf-8")
    ceilings = next(line for line in text.splitlines() if line.startswith("- Ceilings"))

    for constant in (
        runner.MAX_HTML_INPUT_BYTES,
        runner.MAX_ELEMENT_DEPTH,
        runner.MAX_TOKEN_LENGTH,
        runner.MAX_RENDER_PAGES,
        runner.RENDER_TIMEOUT_SECONDS,
        runner.MIN_TOTAL_INK_PIXELS,
    ):
        assert f"`{constant}`" in ceilings, f"evidence predates the {constant} constant"

    table_rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if line.startswith("| ")
    ]
    headers = table_rows[0]
    measured = [dict(zip(headers, cells)) for cells in table_rows[1:]]

    assert len(measured) == len(list(FIXTURES.glob("*.html")))
    # Wall-clock columns would rewrite this file on every regeneration, which is
    # how committed evidence stops meaning anything.
    assert "s" not in headers and "seconds" not in headers
    assert "child spawned" in headers

    for row in measured:
        ink_total = int(row["ink total"].replace(",", ""))
        if row["decision"] == "serve":
            assert ink_total >= runner.MIN_TOTAL_INK_PIXELS
        if row["reason"] == "HtmlOutputVisuallyEmpty":
            assert ink_total == 0
        if row["decision"] == "refuse-intake":
            # The structural fact behind "intake is cheap": no process was
            # spawned, so a refusal cannot cost a render.
            assert row["child spawned"] == "no"
            assert int(row["pages"]) == 0
            assert row["reason"] in {
                "HtmlInputTooLarge",
                "HtmlStructureRejected",
                "HtmlEncodingUnsupported",
                "HtmlInputEmpty",
            }
        else:
            assert row["child spawned"] == "yes"

    assert "rendered a second" in text  # the double-render reproducibility check


# ---------------------------------------------------------------------------
# Wiring - discovery and routing, plus the neighbours that must not move
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def plugin_registry():
    from app.plugins.registry import registry

    return registry


def test_plugin_is_discovered_without_any_registry_edit(plugin_registry):
    """Discovery is an rglob of app/plugins; no central list was touched."""
    assert "html-to-pdf" in plugin_registry.discovery_summary["loaded_plugins"]

    html_skips = [
        item
        for item in plugin_registry.discovery_summary["skipped_plugins"]
        if "html_to_pdf" in str(item)
    ]
    assert html_skips == [], "the plugin was discovered but silently failed to register"


def test_html_to_pdf_and_html_to_csv_do_not_collide(plugin_registry):
    """The registry keys on (source, target) and overwrites silently.

    html-to-csv claims html -> csv; a careless new plugin claiming html -> csv
    too would replace it without any error, so the claim set is asserted.
    """
    pdf_claims = sorted(
        slug
        for slug, pairs in plugin_registry.registered_keys.items()
        if ("html", "pdf") in pairs
    )
    csv_claims = sorted(
        slug
        for slug, pairs in plugin_registry.registered_keys.items()
        if ("html", "csv") in pairs
    )

    assert pdf_claims == ["html-to-pdf"]
    assert csv_claims == ["html-to-csv"]
    assert plugin_registry.get_plugin("html", "pdf").slug == "html-to-pdf"
    assert plugin_registry.get_plugin("html", "csv").slug == "html-to-csv"
    assert plugin_registry.get_plugin("html", "pdf", slug="html-to-pdf").slug == "html-to-pdf"
    # .htm is not claimed by anything: honest scope, no silent support promise.
    with pytest.raises(ValueError):
        plugin_registry.get_plugin("htm", "pdf")


def test_html_to_csv_still_extracts_its_table(tmp_path, plugin_registry):
    source = write_case(
        tmp_path,
        "table.html",
        b"<table><tr><th>a</th><th>b</th></tr><tr><td>1</td><td>2</td></tr></table>",
    )
    work = tmp_path / "csv"

    result = asyncio.run(
        plugin_registry.get_plugin("html", "csv").convert(source, "csv", temp_dir=work)
    )

    assert result.read_text(encoding="utf-8").splitlines()[0] == "a,b"


def test_txt_to_pdf_is_untouched_by_the_new_document_plugin(tmp_path, plugin_registry):
    source = write_case(tmp_path, "notes.txt", b"first line\nsecond line\n")
    work = tmp_path / "txt"

    result = asyncio.run(
        plugin_registry.get_plugin("txt", "pdf").convert(source, "pdf", temp_dir=work)
    )

    assert result.read_bytes().startswith(b"%PDF-")


def test_plugin_refuses_a_target_it_does_not_own(tmp_path):
    """Routing is the service's job, but the plugin still guards its own gate."""
    with pytest.raises(RuntimeError):
        asyncio.run(
            HTMLToPDFPlugin().convert(
                write_case(tmp_path, "page.html", b"<p>hi</p>"),
                "csv",
                temp_dir=tmp_path,
            )
        )


# ---------------------------------------------------------------------------
# Through the real ASGI app - the wiring the plugin cannot see from inside
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def post_html(client, filename: str):
    with fixture_path(filename).open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename, handle, "text/html")},
            data={"target_format": "pdf", "operation": "html-to-pdf"},
        )


def test_upload_serves_a_downloadable_pdf(client):
    response = post_html(client, "valid_utf8.html")

    assert response.status_code == 201, response.text[:300]
    body = response.json()
    assert body["status"] == "success"
    assert body["target_format"] == "pdf"
    assert body["filename"].endswith(".pdf")

    served = client.get(body["download_path"])
    assert served.status_code == 200
    assert served.content.startswith(b"%PDF-")


def test_refused_document_answers_422_without_internal_detail(client):
    response = post_html(client, "oversize_513kb.html")

    assert response.status_code == 422, response.text[:300]
    body = response.json()
    assert body["code"] == "UNSUPPORTED_CONVERSION"
    assert body["message"] == runner.HtmlInputTooLarge.client_message
    for token in FORBIDDEN_CLIENT_TOKENS:
        assert token not in response.text, f"response body leaks {token!r}"


def test_blank_render_answers_422_after_spending_a_real_child(client):
    response = post_html(client, "white_on_white.html")

    assert response.status_code == 422, response.text[:300]
    assert response.json()["message"] == runner.HtmlOutputVisuallyEmpty.client_message







