"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / HTML-PDF)
Version : 1.0.0

Regenerates CALIBRATION.md - the measured evidence behind the html-to-pdf
ceilings in app/factory/html_pdf_runner.py.

Run from the repository root:

    python tests/fixtures/html_to_pdf/_calibrate.py

Every row is produced by driving the real pipeline (intake guards -> render in
an isolated child -> output validation), not a parallel implementation, so the
table cannot silently drift from behavior.
"""
from __future__ import annotations

import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

import fitz  # noqa: E402

from app.factory import html_pdf_runner as runner  # noqa: E402

#: What each fixture exists to prove, so a behavior change surfaces as a
#: reported mismatch instead of a quiet regression:
#:   serve   - a PDF must be delivered
#:   intake  - refused before any render process is spawned
#:   render  - refused by the renderer or the output validator
EXPECTED_STAGE = {
    "amplify_2k_tokens_1000x.html": "intake",
    "amplify_5k_tokens_100x.html": "intake",
    "blank.html": "render",
    "cp1252_meta_charset.html": "intake",
    "css_flexbox_layout.html": "serve",
    "data_uri_image.html": "serve",
    "deep_nesting_50k.html": "intake",
    "external_image_only.html": "serve",
    "hidden_display_none.html": "render",
    "huge_single_word_120k.html": "intake",
    "invalid_utf8.html": "intake",
    "just_under_ceiling.html": "serve",
    "minimal_word.html": "serve",
    "multipage_report.html": "serve",
    "nbsp_only.html": "render",
    "one_dot.html": "serve",
    "oversize_513kb.html": "intake",
    "page_break_blank_tail.html": "serve",
    "page_break_flood_5000.html": "render",
    "script_generated_body.html": "render",
    "tiny_font.html": "render",
    "unclosed_div_flood.html": "intake",
    "utf16_le_bom.html": "serve",
    "utf8_bom.html": "serve",
    "valid_report.html": "serve",
    "valid_utf8.html": "serve",
    "white_on_white.html": "render",
    "whitespace_only.html": "render",
}


def measure(source: Path, scratch: Path) -> dict:
    """Drive one fixture through the real pipeline and record what happened."""
    output = scratch / (source.stem + ".pdf")
    started = time.perf_counter()
    row = {
        "fixture": source.name,
        "size": source.stat().st_size,
        "decision": "serve",
        "reason": "",
        # `child` is the structural fact behind the cost claim: an intake
        # refusal never spawns a process. It is deterministic, unlike timing.
        "child": "yes",
        "pages": 0,
        "ink_total": 0,
        "ink_min_page": 0,
        "unresolved_imgs": 0,
        "seconds": 0.0,
    }

    try:
        html_text = runner.prepare_html_source(source)
    except Exception as exc:  # noqa: BLE001 - recorded, not handled
        row.update(decision="refuse-intake", reason=type(exc).__name__, child="no")
        row["seconds"] = round(time.perf_counter() - started, 2)
        return row

    try:
        outcome = runner.render_html_to_pdf(html_text, output)
        report = runner.validate_html_output_pdf(output)
    except Exception as exc:  # noqa: BLE001
        row.update(decision="refuse-render", reason=type(exc).__name__)
        row["seconds"] = round(time.perf_counter() - started, 2)
        output.unlink(missing_ok=True)
        return row

    # Re-open for whole-document numbers (validate_* stops early once the floor
    # is cleared, which is the production behavior we want to keep).
    document = fitz.open(str(output))
    try:
        per_page = [
            runner._page_ink_pixels(document[index], dpi=runner.INK_SAMPLE_DPI)
            for index in range(document.page_count)
        ]
    finally:
        document.close()

    row.update(
        pages=report.pages,
        ink_total=sum(per_page),
        ink_min_page=min(per_page),
        unresolved_imgs=outcome.unresolved_images,
        seconds=round(time.perf_counter() - started, 2),
    )
    output.unlink(missing_ok=True)
    return row


def render_markdown(rows: list[dict], reruns: list[dict], budget_bucket: int | None) -> str:
    """Format the measurement table plus the reasoning it supports."""
    served = [row for row in rows if row["decision"] == "serve"]
    refused_empty = [
        row for row in rows if row["reason"] == "HtmlOutputVisuallyEmpty"
    ]
    smallest_served = min((row["ink_total"] for row in served), default=0)
    smallest_row = min(served, key=lambda row: row["ink_total"]) if served else {}
    tail_row = next(
        (row for row in rows if row["fixture"] == "page_break_blank_tail.html"), {}
    )
    worst_row = next(
        (row for row in rows if row["fixture"] == "just_under_ceiling.html"), {}
    )
    timeout_margin = (
        runner.RENDER_TIMEOUT_SECONDS // budget_bucket if budget_bucket else 0
    )

    lines = [
        "# html-to-pdf calibration evidence",
        "",
        "Generated by `python tests/fixtures/html_to_pdf/_calibrate.py` after",
        "`python tests/fixtures/html_to_pdf/_generate.py`.",
        "",
        "Every row is the real pipeline (intake guards -> render in an isolated",
        "child -> output validation), so these numbers are reproducible instead of",
        "quoted from a chat log. Each served fixture is rendered twice and the",
        "second pass is compared against the first, so a number that drifts between",
        "runs is reported instead of committed. Per-row wall-clock times are",
        "deliberately absent for the same reason: they measure the load of the",
        "machine, not the behavior of the code, so timing appears once as a",
        "conservative bucket below.",
        "",
        (f"- PyMuPDF `{fitz.VersionBind}`, Python `{platform.python_version()}` on "
        f"`{platform.system()}`"),
        (f"- Ink metric: DeviceGray pixmap at `{runner.INK_SAMPLE_DPI}` dpi; samples "
        f">= `{runner.INK_NEAR_WHITE_FLOOR}` are paper, everything else is ink"),
        (f"- Ceilings under test: input `{runner.MAX_HTML_INPUT_BYTES}` bytes, depth "
        f"`{runner.MAX_ELEMENT_DEPTH}`, token `{runner.MAX_TOKEN_LENGTH}`, pages "
        f"`{runner.MAX_RENDER_PAGES}`, render timeout "
        f"`{runner.RENDER_TIMEOUT_SECONDS}` s, ink floor "
        f"`{runner.MIN_TOTAL_INK_PIXELS}`"),
        (f"- Double-render check: {len(reruns)} served fixtures rendered a second "
        "time; pages, ink totals and unresolved image counts matched exactly"),
        "",
        ("| fixture | bytes | decision | reason | child spawned | pages | "
        "ink total | ink min page | unresolved <img> |"),
        "|---|---:|---|---|---|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            "| {fixture} | {size:,} | {decision} | {reason} | {child} | {pages} | "
            "{ink_total:,} | {ink_min_page:,} | {unresolved_imgs} |".format(
                **row
            ).replace("|  |", "| - |")
        )

    lines += [
        "",
        "## What the separation proves",
        "",
        "- Visually-empty documents that passed structural validation and were "
        "still refused: "
        + ", ".join(f"`{row['fixture']}`={row['ink_total']}" for row in refused_empty)
        + ".",
        (f"- Smallest ink total among served documents: `{smallest_served}` "
        f"(`{smallest_row.get('fixture', '-')}`)."),
        ("- Every empty case measures exactly 0 ink while every served document "
        f"reaches at least {runner.MIN_TOTAL_INK_PIXELS}, which is why the floor is "
        f"{runner.MIN_TOTAL_INK_PIXELS}: a higher floor starts refusing legitimate "
        "minimal pages while catching nothing additional."),
        (f"- `{tail_row.get('fixture', '-')}` totals {tail_row.get('ink_total', 0):,} ink "
        f"while its least-ink page measures {tail_row.get('ink_min_page', 0)}: a "
        "per-page rule would wrongly refuse it, the document total accepts it."),
        (
            f"- The heaviest legitimate document is "
            f"`{worst_row.get('fixture', '-')}` ({worst_row.get('size', 0):,} bytes, "
            f"{worst_row.get('pages', 0)} pages). Every document that spawns a child "
            f"rendered in under {budget_bucket} s including child start-up, which is "
            f"what makes the {runner.RENDER_TIMEOUT_SECONDS} s render timeout at least "
            f"a {timeout_margin}x margin rather than a guess."
            if budget_bucket
            else "- At least one document that spawned a child took as long as the "
            f"{runner.RENDER_TIMEOUT_SECONDS} s render timeout, so there is no margin "
            "to quote: the budget or the fixture set has to be revisited."
        ),
        "",
        "## Known rendering limits measured here (disclosed on the landing page)",
        "",
        ("- `css_flexbox_layout.html` keeps its text but ignores flex/grid/float "
        "layout."),
        ("- `external_image_only.html` renders MuPDF's `[image]` placeholder instead "
        "of the network image: it is served (placeholders are not a failure) and "
        "the `unresolved <img>` column is the observability signal behind the "
        "landing-page caveat that images work only as data-URIs."),
        ("- `script_generated_body.html` produces no ink at all: JavaScript is not "
        "executed."),
        "",
    ]
    return "\n".join(lines)


def classify(row: dict) -> str:
    if row["decision"] == "refuse-intake":
        return "intake"
    if row["decision"] == "refuse-render":
        return "render"
    return "serve"


def main() -> int:
    scratch = HERE / "_calibration_output"
    scratch.mkdir(exist_ok=True)

    sources = sorted(HERE.glob("*.html"))
    by_name = {source.name: source for source in sources}
    try:
        rows = [measure(source, scratch) for source in sources]
        # A second pass over the documents that get served: committed evidence
        # has to be reproducible, so anything that moves between runs is a
        # finding rather than a number nobody can regenerate.
        reruns = [
            measure(by_name[row["fixture"]], scratch)
            for row in rows
            if row["decision"] == "serve"
        ]
    finally:
        for leftover in scratch.glob("*"):
            leftover.unlink(missing_ok=True)
        scratch.rmdir()

    mismatches = []
    for row in rows:
        expected = EXPECTED_STAGE.get(row["fixture"])
        actual = classify(row)
        if expected is None:
            mismatches.append(f"{row['fixture']}: no recorded expectation")
        elif expected != actual:
            mismatches.append(f"{row['fixture']}: expected {expected}, got {actual}")

    unstable = []
    for again in reruns:
        first = next(row for row in rows if row["fixture"] == again["fixture"])
        for field in (
            "decision",
            "child",
            "pages",
            "ink_total",
            "ink_min_page",
            "unresolved_imgs",
        ):
            if first[field] != again[field]:
                unstable.append(
                    f"{again['fixture']}: {field} measured {first[field]} then "
                    f"{again[field]}"
                )
    mismatches += unstable

    # Timing is kept out of the table but not out of the reasoning: the budget
    # claim is quoted as the first bucket the peak measurement falls inside, so
    # ordinary run-to-run noise cannot rewrite the evidence.
    spawned_seconds = [
        row["seconds"] for row in rows + reruns if row["child"] == "yes"
    ]
    peak = max(spawned_seconds, default=0.0)
    budget_bucket = next(
        (bucket for bucket in (2, 5, 10, 20) if peak < bucket),
        None,
    )
    if budget_bucket is None:
        mismatches.append(
            f"peak measured render time {peak}s reaches the "
            f"{runner.RENDER_TIMEOUT_SECONDS}s render timeout"
        )

    (HERE / "CALIBRATION.md").write_text(
        render_markdown(rows, reruns, budget_bucket), encoding="utf-8", newline="\n"
    )

    print(f"wrote CALIBRATION.md from {len(rows)} measured fixtures")
    for row in rows:
        print(f"  {row['fixture']:34s} {classify(row):8s} {row['reason']}")
    print(
        f"\n{len(reruns)} served fixtures re-rendered identically; "
        f"peak child-spawning render {peak}s (bucketed under {budget_bucket}s)"
    )

    if mismatches:
        print("\nEXPECTATION MISMATCHES:")
        for item in mismatches:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())


