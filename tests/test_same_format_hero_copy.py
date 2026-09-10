"""Regression guard for same-format converter hero copy.

Background (F-5 residue, `pdf-metadata` defect):

Converters whose ``source`` and ``target`` are identical (in-place operations
such as pdf-rotate, jpg-crop, pdf-metadata) were originally generated from a
format-pair template that produced a generic hero title:

    "Convert {SOURCE} to {TARGET} Online Free"

For a same-format operation that sentence is meaningless ("Convert PDF to
PDF") and misrepresents the tool as a format conversion instead of an
in-place operation. The F-5 batch corrected the top-level ``title`` of these
slugs but never touched ``hero.title``, which is the field actually rendered
as the page H1 (see app/services/landing_service.py -> build_context).

This guard pins the fix for ``pdf-metadata`` and prevents any *new*
same-format converter from silently shipping the generic hero again.

The allowlist below enumerates the same-format slugs that STILL carry the
generic hero. They are the out-of-scope siblings of the identical defect
(tracked separately, to be remediated as a cluster); they are NOT approved
copy. When one of them is fixed, remove it from this set - the guard is
designed to shrink to empty.
"""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTER_DIR = REPO_ROOT / "app" / "data" / "converters"

#: Same-format slugs that still carry the generic "Convert X to X" hero.
#: SHRINK-ONLY: remove an entry once that slug is remediated. Adding an
#: entry requires the same supervisor approval that `pdf-metadata` needed.
KNOWN_GENERIC_SAME_FORMAT_ALLOWLIST = frozenset(
    {
        "jpg-compress",
        "jpg-crop",
        "jpg-flip",
        "jpg-grayscale",
        "jpg-rotate",
        "jpg-watermark",
        "mp4-compress",
        "pdf-rotate",
        "pdf-unlock",
        "pdf-watermark",
        "png-compress",
    }
)


def _load_converter_data() -> list[tuple[str, dict]]:
    """Load every registry converter JSON (contracts/metadata excluded)."""
    entries: list[tuple[str, dict]] = []
    for path in sorted(CONVERTER_DIR.glob("*.json")):
        if path.name.endswith((".contract.json", ".metadata.json")):
            continue
        with path.open("r", encoding="utf-8") as handle:
            entries.append((path.name, json.load(handle)))
    assert entries, "No converter JSON files were found"
    return entries


def _same_format_slugs(entries: list[tuple[str, dict]]) -> dict[str, str]:
    """Map slug -> hero.title for every source == target converter."""
    result: dict[str, str] = {}
    for _name, data in entries:
        source = str(data.get("source") or "").strip().lower()
        target = str(data.get("target") or "").strip().lower()
        if source and source == target:
            result[str(data.get("slug") or "")] = str(
                (data.get("hero") or {}).get("title") or ""
            )
    return result


def _is_generic_hero(slug: str, hero_title: str) -> bool:
    """True when the hero reads 'Convert {format} to {format}' for a self-pair."""
    source = slug.split("-")[0]
    pattern = re.compile(
        r"^convert\s+%s\s+to\s+%s\b" % (re.escape(source), re.escape(source)),
        re.IGNORECASE,
    )
    return bool(pattern.match(hero_title.strip()))


def test_same_format_converters_do_not_regress_to_generic_hero() -> None:
    entries = _load_converter_data()
    same_format = _same_format_slugs(entries)
    assert same_format, "No same-format converters were found"

    generic = {
        slug
        for slug, hero_title in same_format.items()
        if _is_generic_hero(slug, hero_title)
    }

    unexpected = generic - KNOWN_GENERIC_SAME_FORMAT_ALLOWLIST
    assert not unexpected, (
        "Same-format converter(s) regressed to the generic "
        "'Convert {X} to {X}' hero copy: "
        f"{sorted(unexpected)}. Fix the JSON hero.title or obtain approval "
        "to extend KNOWN_GENERIC_SAME_FORMAT_ALLOWLIST."
    )

    # The allowlist must only reference real same-format slugs (catches stale
    # entries after a slug is renamed or removed).
    stale = KNOWN_GENERIC_SAME_FORMAT_ALLOWLIST - set(same_format)
    assert not stale, f"Allowlist references unknown same-format slugs: {sorted(stale)}"


def test_pdf_metadata_hero_is_not_generic() -> None:
    """Direct pin for the audited defect: pdf-metadata must never be generic."""
    entries = _load_converter_data()
    same_format = _same_format_slugs(entries)

    assert "pdf-metadata" in same_format, "pdf-metadata converter JSON is missing"
    assert not _is_generic_hero("pdf-metadata", same_format["pdf-metadata"]), (
        "pdf-metadata hero.title regressed to 'Convert PDF to PDF'"
    )


def test_pdf_metadata_tool_page_h1_describes_metadata() -> None:
    """End-to-end pin: the rendered H1 must not present a PDF->PDF conversion."""
    client = TestClient(app)
    response = client.get("/tools/pdf-metadata")

    assert response.status_code == 200, response.text
    assert "Convert PDF to PDF" not in response.text

    hero_h1 = re.search(
        r'<h1 class="hero-title">(.*?)</h1>', response.text, re.DOTALL
    )
    assert hero_h1 is not None, "hero-title H1 was not rendered"
    assert "metadata" in hero_h1.group(1).lower()