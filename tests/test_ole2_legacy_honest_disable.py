"""
PR-1 (OLE2 honest-disable) regression suite.

Pins the four layers of the fix for legacy binary Office (.xls/.doc/.ppt) files,
which live in the OLE2 / Compound File Binary container and cannot be read by
openpyxl / python-docx / python-pptx:

  1. upload gate      -> 415 + explicit re-save guidance (never a 500)
  2. registry         -> dead-end legacy SOURCE pairs are not registered
  3. converter layer  -> honest 422 UNSUPPORTED_CONVERSION for OLE2 bytes that
                         hide behind an OOXML filename (the upload gate cannot
                         catch these: the container signature check is skipped
                         when the MIME matches)
  4. advertising      -> no converter JSON / contract / UI row claims .xls, .doc
                         or .ppt as an input

It also pins the two things that must NOT regress: supported OOXML conversions
still work, and a legacy *target* token still resolves to a correctly named
OOXML file (the alias contract tested by test_009_doc_alias_converts_to_docx).
"""

from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.plugins import discover_plugins
from app.plugins.registry import registry
from app.services.conversion_service import UnsupportedConversionError
from app.utils.file_validator import (
    ALLOWED_EXTENSIONS,
    FileValidationError,
    validate_extension,
)
from app.utils.legacy_office import (
    LEGACY_OFFICE_REPLACEMENTS,
    OLE2_MAGIC,
    detect_container,
    legacy_format_unsupported_error,
)

# A minimal but genuine OLE2 header: enough for magic-byte detection, and
# exactly what openpyxl / python-docx / python-pptx choke on.
OLE2_BYTES = OLE2_MAGIC + b"\x00" * 504

LEGACY_CASES = [
    pytest.param("xls", "application/vnd.ms-excel", id="xls"),
    pytest.param("doc", "application/msword", id="doc"),
    pytest.param("ppt", "application/vnd.ms-powerpoint", id="ppt"),
]

# Real OOXML fixtures (the loose tests/sample.* placeholders are not valid).
ASSETS = Path("tests/assets/regression")
SAMPLES = {
    "docx": ASSETS / "sample.docx",
    "xlsx": ASSETS / "sample.xlsx",
    "pptx": ASSETS / "sample.pptx",
}

_INTERNAL_MARKERS = (
    "Traceback",
    "openpyxl",
    "python-docx",
    "python-pptx",
    "DocxDocument",
    "Presentation",
    "load_workbook",
    "PackageNotFoundError",
    "BadZipFile",
    "InvalidFileException",
    "uploads\\",
    "uploads/",
    ".venv",
    "site-packages",
)


def assert_no_internal_leak(message: str) -> None:
    leaked = [m for m in _INTERNAL_MARKERS if m.lower() in message.lower()]
    assert not leaked, f"internal detail leaked to client: {leaked} in {message!r}"


# ---------------------------------------------------------------------------
# 1. upload gate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("legacy_ext,mime", LEGACY_CASES)
def test_legacy_extension_is_not_accepted(legacy_ext: str, mime: str) -> None:
    """The dead-end legacy extensions are out of the upload allow-list."""
    assert legacy_ext not in ALLOWED_EXTENSIONS


@pytest.mark.parametrize("legacy_ext,mime", LEGACY_CASES)
def test_legacy_extension_rejection_carries_resave_guidance(
    legacy_ext: str, mime: str
) -> None:
    """Rejection names the format and the modern replacement, not a stack trace."""
    modern = LEGACY_OFFICE_REPLACEMENTS[legacy_ext]

    with pytest.raises(FileValidationError) as excinfo:
        validate_extension(f"report.{legacy_ext}")

    message = str(excinfo.value)
    assert f".{legacy_ext}" in message, message
    assert f".{modern}" in message, message
    assert_no_internal_leak(message)


@pytest.mark.parametrize("legacy_ext,mime", LEGACY_CASES)
def test_legacy_upload_returns_415_not_500(
    legacy_ext: str, mime: str, tmp_path: Path
) -> None:
    """A real .xls/.doc/.ppt upload is refused with 415 + guidance."""
    modern = LEGACY_OFFICE_REPLACEMENTS[legacy_ext]
    client = TestClient(app)

    response = client.post(
        "/convert",
        files={"file": (f"legacy.{legacy_ext}", OLE2_BYTES, mime)},
        data={"target_format": "pdf"},
    )

    assert response.status_code == 415, response.text
    body = response.json()
    assert body["code"] == "UNSUPPORTED_FILE_TYPE", body
    message = body["message"]
    assert f"Legacy .{legacy_ext}" in message, message
    assert f".{modern}" in message, message
    assert_no_internal_leak(message)



# ---------------------------------------------------------------------------
# 2. registry: the dead-end pairs must not exist at all
# ---------------------------------------------------------------------------

def test_no_registered_pair_has_a_legacy_source() -> None:
    """No converter may claim .xls/.doc/.ppt as an input any more."""
    offenders = sorted(
        f"{src}->{tgt}"
        for (src, tgt) in registry.plugins
        if src in LEGACY_OFFICE_REPLACEMENTS
    )
    assert offenders == [], f"legacy source pairs still registered: {offenders}"


def test_no_plugin_declares_a_legacy_source_format() -> None:
    """Plugin metadata itself must not advertise legacy inputs."""
    offenders: list[str] = []
    for plugin_class in discover_plugins().plugin_classes:
        for source in getattr(plugin_class, "source_formats", []) or []:
            if source.lower() in LEGACY_OFFICE_REPLACEMENTS:
                offenders.append(
                    f"{getattr(plugin_class, 'slug', plugin_class.__name__)}:{source}"
                )
    assert offenders == [], f"plugins still declare legacy sources: {offenders}"


@pytest.mark.parametrize(
    "source,target",
    [
        ("xls", "pdf"), ("xls", "docx"), ("xls", "pptx"),
        ("doc", "pdf"), ("doc", "xlsx"), ("doc", "pptx"),
        ("ppt", "pdf"), ("ppt", "docx"), ("ppt", "xlsx"), ("ppt", "jpg"),
    ],
)
def test_legacy_input_pairs_are_not_routable(source: str, target: str) -> None:
    """A dead-end pair is simply not in the registry (-> 422 at the service)."""
    with pytest.raises(ValueError):
        registry.get_plugin(source, target)


# ---------------------------------------------------------------------------
# 3. converter layer: OLE2 bytes behind an OOXML name -> honest 422
# ---------------------------------------------------------------------------

OOXML_MIME = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

MASQUERADE_CASES = [
    pytest.param("xlsx", "pdf", None, id="xlsx-pdf"),
    pytest.param("docx", "pdf", None, id="docx-pdf"),
    pytest.param("pptx", "pdf", None, id="pptx-pdf"),
    pytest.param("docx", "jpg", "docx-to-jpg", id="docx-jpg"),
    pytest.param("pptx", "jpg", "ppt-to-jpg", id="pptx-jpg"),
]


@pytest.mark.parametrize("modern_ext,target,operation", MASQUERADE_CASES)
def test_ole2_behind_ooxml_name_returns_422_not_500(
    modern_ext: str, target: str, operation: str | None
) -> None:
    """The signature gate is skipped for matching MIME, so converters must guard.

    Before PR-1 each of these returned HTTP 500 and echoed library text such as
    "BadZipFile: File is not a zip file" or a server upload path.
    """
    client = TestClient(app)
    data = {"target_format": target}
    if operation:
        data["operation"] = operation

    response = client.post(
        "/convert",
        files={"file": (f"masquerade.{modern_ext}", OLE2_BYTES, OOXML_MIME[modern_ext])},
        data=data,
    )

    assert response.status_code == 422, response.text
    body = response.json()
    assert body["code"] == "UNSUPPORTED_CONVERSION", body
    assert "ole2" in body["message"].lower(), body
    assert modern_ext in body["message"].lower(), body
    assert_no_internal_leak(body["message"])


def test_legacy_error_type_and_hierarchy() -> None:
    """The shared error subclasses UnsupportedConversionError (which maps to 422)."""
    error = legacy_format_unsupported_error("ppt", "pdf")

    assert isinstance(error, UnsupportedConversionError)
    assert type(error).__name__ == "LegacyFormatUnsupportedError"
    assert error.source_format == "ppt"
    assert error.target_format == "pdf"
    assert_no_internal_leak(str(error))


# ---------------------------------------------------------------------------
# 4. advertising: no artifact may promise a legacy input
# ---------------------------------------------------------------------------

CONVERTER_DATA = Path("app/data/converters")
AUDITED_ARTIFACTS = [
    "excel-to-pdf.json",
    "excel-to-pdf.metadata.json",
    "excel-to-pdf.contract.json",
    "ppt-to-pdf.json",
    "ppt-to-pdf.metadata.json",
    "word-to-pdf.metadata.json",
    "ppt-to-pdf.contract.json",
    "ppt-to-jpg.contract.json",
    "ppt-to-docx.contract.json",
    "ppt-to-xlsx.contract.json",
    "docx-to-jpg.contract.json",
    "docx-to-xlsx.contract.json",
    "docx-to-ppt.contract.json",
    "xlsx-to-docx.contract.json",
    "xlsx-to-ppt.contract.json",
]


@pytest.mark.parametrize("artifact", AUDITED_ARTIFACTS)
def test_converter_artifact_has_no_legacy_input(artifact: str) -> None:
    """Contracts/metadata feed authority + comparison pages, so they must be true."""
    import json

    payload = json.loads((CONVERTER_DATA / artifact).read_text(encoding="utf-8"))
    inputs = {str(item).lower() for item in payload.get("input_formats", [])}
    assert not (inputs & set(LEGACY_OFFICE_REPLACEMENTS)), f"{artifact}: {inputs}"

    accept = str(payload.get("accept", ""))
    for legacy_ext in LEGACY_OFFICE_REPLACEMENTS:
        assert f".{legacy_ext}" not in accept, f"{artifact}: accept={accept}"


def test_ui_dropdown_has_no_legacy_source_rows() -> None:
    """STATIC_TARGET_MAP must not offer rows for formats we refuse to accept."""
    html = Path("app/templates/main/converigo_main.html").read_text(encoding="utf-8")
    block = html.split("const STATIC_TARGET_MAP = {", 1)[1].split("};", 1)[0]
    keys = {
        key.strip("'\"").lower()
        for key, _values in re.findall(r"(['\"a-zA-Z0-9_]+):\[(.*?)\]", block)
    }
    assert not (keys & set(LEGACY_OFFICE_REPLACEMENTS)), sorted(keys)


# ---------------------------------------------------------------------------
# 5. non-regression: everything that genuinely works must keep working
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("modern_ext", ["docx", "xlsx", "pptx"])
def test_ooxml_fixtures_are_genuine_zip_containers(modern_ext: str) -> None:
    """Guard against the placeholder fixtures silently replacing real ones."""
    sample = SAMPLES[modern_ext]
    assert sample.exists(), f"missing fixture {sample}"
    assert detect_container(sample) == "zip", f"{sample} is not a real OOXML file"


@pytest.mark.parametrize(
    "modern_ext,target,operation",
    [
        ("pptx", "pdf", "ppt-to-pdf"),
        ("pptx", "jpg", "ppt-to-jpg"),
        ("docx", "jpg", "docx-to-jpg"),
        ("docx", "pdf", "word-to-pdf"),
        ("xlsx", "pdf", "excel-to-pdf"),
        ("xlsx", "docx", "xlsx-to-docx"),
    ],
)
def test_supported_ooxml_conversions_still_work(
    modern_ext: str, target: str, operation: str
) -> None:
    """PR-1 restricts legacy inputs only; supported pairs must be untouched."""
    sample = SAMPLES[modern_ext]
    client = TestClient(app)

    response = client.post(
        "/convert",
        files={"file": (sample.name, sample.read_bytes(), OOXML_MIME[modern_ext])},
        data={"target_format": target, "operation": operation},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["status"] == "success", payload
    assert payload["download_path"].endswith(f".{target}"), payload


def test_legacy_target_alias_still_produces_correctly_named_ooxml() -> None:
    """The alias contract stays: asking for a legacy target yields a real modern
    file whose NAME says so (never a mislabelled artifact)."""
    sample = Path("tests/sample.pdf")
    assert sample.exists()
    client = TestClient(app)

    response = client.post(
        "/convert",
        files={"file": (sample.name, sample.read_bytes(), "application/pdf")},
        data={"target_format": "doc", "operation": "pdf-to-word"},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["filename"].endswith(".docx"), payload
    assert not payload["filename"].endswith(".doc"), payload


# ---------------------------------------------------------------------------
# 6. honest restriction must NOT de-index a certified route
# ---------------------------------------------------------------------------

# Removing the legacy input pairs must not change a route's index presence.
# Availability for a tool page is derived from its declared source/target pair
# (converter_data_service._is_supported_converter), so tools whose slug names a
# legacy format must declare the OOXML input they really accept instead of
# keeping the dead pair registered. Sitemap presence additionally honours the
# pre-existing ledger-derived de-index policy (SEARCH_INDEX_DISABLED_SLUGS),
# which is a separate tracked governance concern and is therefore accepted as-is
# here rather than re-implemented.
CERTIFIED_ROUTES_MUST_STAY_LISTED = [
    "ppt-to-docx",
    "ppt-to-xlsx",
    "ppt-to-pdf",
    "ppt-to-jpg",
    "docx-to-jpg",
    "docx-to-ppt",
    "docx-to-xlsx",
    "excel-to-pdf",
    "xlsx-to-docx",
    "xlsx-to-ppt",
    "word-to-pdf",
]


def test_honest_disable_does_not_deindex_certified_routes() -> None:
    from app.services.converter_data_service import (
        SEARCH_INDEX_DISABLED_SLUGS,
        ConverterDataService,
    )

    service = ConverterDataService(CONVERTER_DATA)
    supported = {str(tool.get("slug")) for tool in service.list_supported_converters()}
    missing = [slug for slug in CERTIFIED_ROUTES_MUST_STAY_LISTED if slug not in supported]
    assert not missing, f"certified routes dropped from the converter list: {missing}"

    locs = {
        entry["loc"].rstrip("/")
        for entry in service.sitemap_entries("https://converigo.com")
    }
    silently_gone = [
        slug
        for slug in CERTIFIED_ROUTES_MUST_STAY_LISTED
        if f"https://converigo.com/tools/{slug}" not in locs
        and slug not in SEARCH_INDEX_DISABLED_SLUGS
    ]
    assert not silently_gone, (
        f"routes missing from the sitemap without a policy reason: {silently_gone}"
    )


def test_no_active_converter_advertises_a_legacy_source() -> None:
    """No indexed tool page may declare a legacy OLE2 format as its input.

    The converter list is what feeds the sitemap, hub pages, recommendations and
    authority copy, so a stale `source` here republishes the phantom capability
    even when the plugin layer refuses the file.
    """
    from app.services.converter_data_service import ConverterDataService

    service = ConverterDataService(CONVERTER_DATA)
    offenders = [
        str(tool.get("slug"))
        for tool in service.list_active_converters()
        if str(tool.get("source", "")).strip().lower() in LEGACY_OFFICE_REPLACEMENTS
    ]
    assert offenders == [], f"tool pages still advertise a legacy OLE2 input: {offenders}"
