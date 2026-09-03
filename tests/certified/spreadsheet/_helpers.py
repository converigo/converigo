"""
PROJECT: CONVERIGO
TEST SUITE: Certified Spreadsheet / Data Pipeline Converters (Batch 1)

Shared helpers for creating real file samples and verifying conversion output.
"""

from __future__ import annotations

import csv as csv_mod
import json
from pathlib import Path

ROWS = [
    {"id": 1, "name": "alpha", "score": 95.5, "active": True},
    {"id": 2, "name": "beta", "score": 87.25, "active": False},
    {"id": 3, "name": "gamma", "score": 42.0, "active": True},
]
CSV_COLUMNS = ["id", "name", "score", "active"]


def _write_csv(path: Path) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv_mod.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(ROWS)
    return path


def _write_json(path: Path) -> Path:
    path.write_text(json.dumps(ROWS), encoding="utf-8")
    return path


def _write_xlsx(path: Path) -> Path:
    from openpyxl import Workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "data"
    sheet.append(CSV_COLUMNS)
    for row in ROWS:
        sheet.append([row[c] for c in CSV_COLUMNS])
    workbook.save(str(path))
    return path


def _read_rows_from_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv_mod.DictReader(handle))
    return [
        {
            "id": int(r["id"]),
            "name": str(r["name"]),
            "score": float(r["score"]),
            "active": str(r["active"]).strip().lower() in ("true", "1"),
        }
        for r in rows
    ]


def _read_rows_from_xlsx(path: Path) -> list[dict]:
    import pandas as pd
    frame = pd.read_excel(path)
    records = frame.to_dict(orient="records")
    return [
        {"id": int(r["id"]), "name": str(r["name"]),
         "score": float(r["score"]), "active": bool(r["active"])}
        for r in records
    ]


def _read_rows_from_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_rows_equivalent(actual: list[dict], expected: list[dict]) -> None:
    assert len(actual) == len(expected), f"row count mismatch: {len(actual)} != {len(expected)}"
    for got, want in zip(actual, expected):
        assert int(got["id"]) == int(want["id"])
        assert str(got["name"]) == str(want["name"])
        assert abs(float(got["score"]) - float(want["score"])) < 1e-6
        assert bool(got["active"]) == bool(want["active"])
