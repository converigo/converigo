"""PR-A1: Certified XLSX to ODS converter tests.

Verifies that XLSX->ODS conversion produces a real, valid ODS file
with the correct content integrity.
"""

from pathlib import Path

from fastapi.testclient import TestClient
from odf import teletype
from odf.opendocument import load as ods_load
from odf.table import Table, TableCell, TableRow

from app.core.settings import settings
from app.main import app


def _extract_ods_cell_values(ods_path: Path) -> list[list[str]]:
    """Extract cell values from an ODS spreadsheet table."""
    doc = ods_load(str(ods_path))
    sheets = doc.spreadsheet.getElementsByType(Table)
    rows_data: list[list[str]] = []
    for sheet in sheets:
        for table_row in sheet.getElementsByType(TableRow):
            row_values: list[str] = []
            for cell in table_row.getElementsByType(TableCell):
                value_type = cell.getAttribute("valuetype") or "string"
                if value_type == "float":
                    raw = cell.getAttribute("value")
                    row_values.append(str(raw) if raw is not None else "")
                elif value_type == "boolean":
                    raw = cell.getAttribute("booleanvalue")
                    row_values.append(str(raw) if raw is not None else "")
                elif value_type == "date":
                    row_values.append(cell.getAttribute("datevalue") or "")
                else:
                    # odfpy Element has no textContent; use teletype.extractText(),
                    # the standard odfpy API for extracting text from ODF elements.
                    text = (teletype.extractText(cell) or "").strip()
                    row_values.append(text)
            if any(v for v in row_values):
                rows_data.append(row_values)
    return rows_data


def test_xlsx_to_ods_conversion_creates_valid_ods(tmp_path: Path):
    client = TestClient(app)

    xlsx_path = Path("tests/sample.xlsx")
    assert xlsx_path.exists(), "Sample XLSX is missing"

    resp = client.post(
        "/convert",
        data={"target_format": "ods", "operation": "xlsx-to-ods"},
        files={
            "file": (
                xlsx_path.name,
                xlsx_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload.get("status") == "success"
    download_path = payload.get("download_path")
    assert download_path, payload
    assert download_path.startswith("/download/")
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2, f"Unexpected download path shape: {download_path}"
    conversion_id, filename = relative_parts
    assert filename.endswith(".ods")

    local_path = settings.OUTPUT_DIR / conversion_id / filename
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"

    assert local_path.exists(), f"Expected output ODS not found: {local_path}"
    assert local_path.stat().st_size > 0, "Output ODS is empty"
    assert local_path.suffix.lower() == ".ods"

    assert len(list((settings.OUTPUT_DIR / conversion_id).glob("*"))) == 1


def test_xlsx_to_ods_content_integrity(tmp_path: Path):
    """Verify the output ODS contains the data from the source XLSX."""
    client = TestClient(app)

    xlsx_path = Path("tests/sample.xlsx")
    resp = client.post(
        "/convert",
        data={"target_format": "ods", "operation": "xlsx-to-ods"},
        files={
            "file": (
                xlsx_path.name,
                xlsx_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    conversion_id, filename = Path(payload["download_path"].removeprefix("/download/")).parts
    local_path = settings.OUTPUT_DIR / conversion_id / filename

    try:
        doc = ods_load(str(local_path))
        sheets = doc.spreadsheet.getElementsByType(Table)
        assert len(sheets) >= 1, "Expected at least one sheet in ODS output"

        # Check sheet name
        sheet0_name = sheets[0].getAttribute("name") or ""
        assert "Sheet" in sheet0_name, f"Expected 'Sheet' sheet, got '{sheet0_name}'"

        rows_data = _extract_ods_cell_values(local_path)
        assert len(rows_data) >= 1, "Expected at least one data row in ODS"

        joined = ", ".join([", ".join(r) for r in rows_data])
        assert "Hello" in joined, f"Expected 'Hello' in ODS cells, got: {joined[:500]}"
        assert "World" in joined, f"Expected 'World' in ODS cells, got: {joined[:500]}"
    finally:
        local_path.unlink(missing_ok=True)


def test_xlsx_to_ods_output_is_real_ods():
    """Verify the output starts with ODF magic bytes and has correct mimetype."""
    client = TestClient(app)

    xlsx_path = Path("tests/sample.xlsx")
    resp = client.post(
        "/convert",
        data={"target_format": "ods", "operation": "xlsx-to-ods"},
        files={
            "file": (
                xlsx_path.name,
                xlsx_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    conversion_id, filename = Path(payload["download_path"].removeprefix("/download/")).parts
    local_path = settings.OUTPUT_DIR / conversion_id / filename

    try:
        with local_path.open("rb") as handle:
            header = handle.read(4)
        # ODF files start with PK\x03\x04 (ZIP) and contain mimetype entry
        assert header == b"PK\x03\x04", f"Output is not a real ODS (ZIP) file: {header!r}"

        # Verify it's a valid ODS via odfpy
        doc = ods_load(str(local_path))
        assert doc.mimetype == "application/vnd.oasis.opendocument.spreadsheet", (
            f"Unexpected mimetype: {doc.mimetype}"
        )
    finally:
        local_path.unlink(missing_ok=True)