"""
PROJECT: CONVERIGO
TEST SUITE: Certified Document Factory Cluster - Factory Batch F7 (Jalur 2)

Factory Batch F7 (office/document cluster): the two net-new document
converters (DOC-14 docx-to-html via mammoth; pptx-to-png via the certified
python-pptx -> reportlab -> PyMuPDF engine pipeline).  ONE parametric test
file for the whole F7 batch, using the shared factory harness uniform
contract:

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    output content verified -> honest 422 UNSUPPORTED_CONVERSION

Governance note: tracked regression samples exist for BOTH source formats
(tests/assets/regression/sample.docx, tests/assets/regression/sample.pptx),
so per the F4-validated tracked-sample policy F7 ships full office-cluster
contract artifacts (<slug>.contract.json + <slug>.json landing pages) - the
docx-to-jpg precedent, asserted below.  Runtime uploads use the
regression-circuit samples (office-suite precedent, tests/certified/office)
because the loose tests/sample.docx is a text placeholder, not a real OOXML
container; the contract metadata still references tests/sample.<ext> like
every office-cluster contract.

Dependency note: mammoth>=1.11.0 is mandatory (CVE-2025-11849 affects
mammoth 0.3.25 - < 1.11.0); requirements.txt pins the floor.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from PIL import Image

from tests.certified._factory_harness import (
    assert_honest_unsupported,
    cleanup_output,
    post_convert,
    run_happy_path,
)

# Office-suite precedent (tests/certified/office/*): real containers are
# uploaded with the generic octet-stream MIME so the strict signature gate
# (PK magic) stays exercised.
OFFICE_MIME = "application/octet-stream"

# Runtime uploads use the tracked regression-circuit samples (office-suite
# precedent: tests/certified/office/* posts tests/assets/regression files):
# the loose tests/sample.docx is a text placeholder, not a real OOXML
# container, so the strict signature gate would reject it before conversion.
RUNTIME_DOCX_SAMPLE = Path("tests/assets/regression/sample.docx")
RUNTIME_PPTX_SAMPLE = Path("tests/assets/regression/sample.pptx")
TXT_SAMPLE = Path("tests/sample.txt")

# PK-prefixed junk: passes the ZIP signature gate, but is not a real OOXML
# container, so the conversion layer must still fail honestly.
CORRUPT_OOXML_JUNK = b"PK\x03\x04" + b"not-a-real-ooxml-container" * 8

F7_CASES = [
    ("docx-to-html", "html", RUNTIME_DOCX_SAMPLE),
    ("pptx-to-png", "png", RUNTIME_PPTX_SAMPLE),
]

F7_SLUGS = [slug for slug, _, _ in F7_CASES]


def _docx_paragraph_texts() -> list[str]:
    """Ground truth: text extracted from the tracked sample with python-docx."""
    from docx import Document

    document = Document(str(RUNTIME_DOCX_SAMPLE))
    return [p.text.strip() for p in document.paragraphs if p.text.strip()]


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.chunks.append(data.strip())


def _verify_html(output_path: Path) -> None:
    text = output_path.read_text(encoding="utf-8")
    assert text.startswith("<!DOCTYPE html>"), text[:64]
    assert '<meta charset="utf-8">' in text
    assert "<body>" in text and "</body>" in text

    extractor = _TextExtractor()
    extractor.feed(text)
    rendered = " ".join(extractor.chunks)

    expected = _docx_paragraph_texts()
    assert expected, "sample.docx unexpectedly contains no paragraph text"
    matched = [paragraph for paragraph in expected if paragraph in rendered]
    assert matched, (
        f"None of the DOCX paragraph texts survived conversion; "
        f"expected one of {expected[:3]!r} in rendered text."
    )


def _verify_png(output_path: Path) -> None:
    assert output_path.stat().st_size > 0, "Output PNG is empty"
    with Image.open(str(output_path)) as image:
        assert image.format == "PNG", image.format
        assert image.width > 0 and image.height > 0


_VERIFIERS = {
    "docx-to-html": _verify_html,
    "pptx-to-png": _verify_png,
}


# ---------------------------------------------------------------------------
# Uniform factory contract: discovery -> 201 -> download 200 -> verified output
# ---------------------------------------------------------------------------


@pytest.mark.certified
@pytest.mark.parametrize(
    ("slug", "target_format", "sample"),
    F7_CASES,
    ids=[slug for slug, _, _ in F7_CASES],
)
def test_factory_conversion_happy_path(
    slug: str, target_format: str, sample: Path
) -> None:
    """Tracked regression sample converts end-to-end with verified content."""
    assert sample.exists(), f"tracked regression sample missing: {sample}"
    output = run_happy_path(sample, target_format, slug, mime=OFFICE_MIME)
    try:
        _VERIFIERS[slug](output)
    finally:
        cleanup_output(output)


# ---------------------------------------------------------------------------
# Honest errors: unsupported source + signature-gate-passing corrupt container
# ---------------------------------------------------------------------------


@pytest.mark.certified
@pytest.mark.parametrize(
    ("slug", "target_format"),
    [(slug, target) for slug, target, _ in F7_CASES],
    ids=F7_SLUGS,
)
def test_factory_unsupported_source(slug: str, target_format: str) -> None:
    """A tracked non-office sample must fail honestly, never fabricate output."""
    assert TXT_SAMPLE.exists(), f"tracked sample missing: {TXT_SAMPLE}"
    response = post_convert(TXT_SAMPLE, target_format, slug)
    assert_honest_unsupported(response)


@pytest.mark.certified
@pytest.mark.parametrize(
    ("slug", "target_format"),
    [(slug, target) for slug, target, _ in F7_CASES],
    ids=F7_SLUGS,
)
def test_factory_honest_error_for_corrupt_input(
    slug: str, target_format: str, tmp_path: Path
) -> None:
    """PK-prefixed junk passes the ZIP signature gate but is not OOXML:
    conversion must fail honestly (422 UNSUPPORTED_CONVERSION), never 500."""
    extension = "docx" if slug == "docx-to-html" else "pptx"
    corrupt = tmp_path / f"corrupt.{extension}"
    corrupt.write_bytes(CORRUPT_OOXML_JUNK)
    response = post_convert(corrupt, target_format, slug)
    assert_honest_unsupported(response)


# ---------------------------------------------------------------------------
# Governance artifacts: F7 follows the office-cluster CONTRACT path
# ---------------------------------------------------------------------------


@pytest.mark.certified
def test_static_target_map_f7_rows() -> None:
    """The deployed STATIC_TARGET_MAP rows reflect the F7 delta: docx gains
    HTML, pptx gains PNG (registry-derived, alphabetically sorted)."""
    html_text = Path("app/templates/main/converigo_main.html").read_text(
        encoding="utf-8"
    )
    block = html_text.split("const STATIC_TARGET_MAP = {", 1)[1].split("};", 1)[0]
    mapping: dict[str, list[str]] = {}
    for key, values in re.findall(r"(['\"a-zA-Z0-9_]+):\[(.*?)\]", block):
        mapping[key.strip("'\"")] = [
            v.strip().strip("'\"") for v in values.split(",") if v.strip()
        ]

    assert mapping.get("docx") == [
        "HTML", "JPEG", "JPG", "PDF", "POWERPOINT", "PPT", "PPTX",
        "SPREADSHEET", "XLS", "XLSX",
    ], mapping.get("docx")
    assert mapping.get("pptx") == [
        "DOC", "DOCX", "JPEG", "JPG", "PDF", "PNG", "SPREADSHEET", "WORD",
        "XLS", "XLSX",
    ], mapping.get("pptx")


@pytest.mark.certified
def test_contract_artifacts_shipped() -> None:
    """Both F7 slugs ship office-cluster-style artifacts: <slug>.contract.json
    + <slug>.json landing page.  Contract metadata references the loose
    tests/sample.<ext> pointer (office-cluster precedent); the regression
    circuit samples exercised by the happy-path test above are tracked too."""
    converters_dir = Path("app/data/converters")
    contract_samples = {
        "docx-to-html": Path("tests/sample.docx"),
        "pptx-to-png": Path("tests/sample.pptx"),
    }
    for slug, sample in contract_samples.items():
        contract_path = converters_dir / f"{slug}.contract.json"
        assert contract_path.is_file(), f"missing contract artifact: {contract_path.name}"
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
        assert payload.get("slug") == slug, payload.get("slug")
        assert payload.get("lifecycle_status") == "certified", payload.get("lifecycle_status")
        assert payload.get("conversion_engine") == "document", payload.get("conversion_engine")

        regression_sample = Path(payload["regression_sample"])
        assert regression_sample == sample, payload["regression_sample"]
        assert regression_sample.is_file(), (
            f"contract regression sample missing on disk: {regression_sample}"
        )

        page_path = converters_dir / f"{slug}.json"
        assert page_path.is_file(), f"missing page artifact: {page_path.name}"
        page = json.loads(page_path.read_text(encoding="utf-8"))
        assert page.get("slug") == slug, page.get("slug")
        assert page.get("lifecycle_status") == "certified", page.get("lifecycle_status")


@pytest.mark.certified
def test_requirements_pin_mammoth_floor() -> None:
    """mammoth>=1.11.0 is mandatory: CVE-2025-11849 affects 0.3.25 - < 1.11.0."""
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    match = re.search(r"^mammoth>=([0-9.]+)\s*$", requirements, re.MULTILINE)
    assert match, "requirements.txt must pin mammoth>=1.11.0"
    major, minor = (int(part) for part in match.group(1).split(".")[:2])
    assert (major, minor) >= (1, 11), match.group(1)