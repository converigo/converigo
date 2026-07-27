#!/usr/bin/env python3
"""Validate expected generated metadata files and report readiness."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import generated_dir, write_text

REQUIRED_FILES = [
    "project_index.json",
    "module_index.json",
    "project_map.json",
    "routes.json",
    "services.json",
    "converters.json",
    "import_map.json",
    "knowledge_summary.json",
    "context.json",
]


@dataclass(frozen=True)
class ValidationResult:
    name: str
    exists: bool
    valid_json: bool
    size_bytes: int
    message: str


def validate_json_file(path: Path, name: str) -> ValidationResult:
    """Validate presence and JSON parseability of a required metadata file."""
    if not path.exists() or not path.is_file():
        return ValidationResult(name=name, exists=False, valid_json=False, size_bytes=0, message="missing")

    size = path.stat().st_size
    try:
        with path.open("r", encoding="utf-8") as file_obj:
            json.load(file_obj)
    except json.JSONDecodeError as exc:
        return ValidationResult(
            name=name,
            exists=True,
            valid_json=False,
            size_bytes=size,
            message=f"invalid json: {exc}",
        )

    return ValidationResult(name=name, exists=True, valid_json=True, size_bytes=size, message="ok")


def render_report(results: list[ValidationResult], generated: Path) -> str:
    """Render a readable plain-text validation report."""
    ok_count = sum(1 for result in results if result.exists and result.valid_json)
    total = len(results)

    lines: list[str] = []
    lines.append("AI_BRAIN Metadata Health Check")
    lines.append("=" * 30)
    lines.append(f"Generated directory: {generated.as_posix()}")
    lines.append(f"Valid files: {ok_count}/{total}")
    lines.append("")
    lines.append("File Status")
    lines.append("-" * 30)

    for result in results:
        status = "OK" if result.exists and result.valid_json else "FAIL"
        lines.append(
            f"[{status}] {result.name} | exists={result.exists} | valid_json={result.valid_json} | "
            f"size={result.size_bytes} | {result.message}"
        )

    lines.append("")
    lines.append("Overall")
    lines.append("-" * 30)
    lines.append("PASS" if ok_count == total else "FAIL")
    lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Validate AI_BRAIN generated metadata files")
    parser.add_argument("--generated-dir", type=Path, default=generated_dir(), help="Generated metadata directory")
    parser.add_argument(
        "--report-file",
        type=Path,
        default=None,
        help="Optional report output path (default: generated/health_report.txt)",
    )
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    generated = args.generated_dir.resolve()

    if not generated.exists() or not generated.is_dir():
        raise SystemExit(f"Invalid --generated-dir: {generated}")

    results = [validate_json_file(generated / name, name) for name in REQUIRED_FILES]
    report = render_report(results, generated)

    report_file = args.report_file.resolve() if args.report_file else generated / "health_report.txt"
    write_text(report_file, report)
    print(report)


if __name__ == "__main__":
    main()
