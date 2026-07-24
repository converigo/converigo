#!/usr/bin/env python3
"""Generate module_summary.md from module_index.json.

Input:
- AI_BRAIN/generated/module_index.json

Output:
- AI_BRAIN/generated/module_summary.md

The script reads only module_index.json and produces a metadata-only markdown summary.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import generated_dir, load_json, write_text

INPUT_FILE = "module_index.json"
OUTPUT_FILE = "module_summary.md"


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def first_non_empty_string(record: dict[str, Any], keys: list[str]) -> str:
    """Return first non-empty string value for the provided keys."""
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_name_list(value: Any) -> list[str]:
    """Extract a list of names from list-like fields without inventing values."""
    names: list[str] = []

    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
            elif isinstance(item, dict):
                name = first_non_empty_string(item, ["name", "id", "symbol"])
                if name:
                    names.append(name)
    return names


def discover_module_records(payload: Any) -> list[dict[str, Any]]:
    """Discover module records from common module-index structures."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        if isinstance(payload.get("modules"), list):
            return [item for item in payload["modules"] if isinstance(item, dict)]

        records: list[dict[str, Any]] = []
        for value in payload.values():
            if isinstance(value, dict):
                records.append(value)
            elif isinstance(value, list):
                records.extend(item for item in value if isinstance(item, dict))
        return records

    return []


def normalize_module_record(record: dict[str, Any], fallback_index: int) -> dict[str, Any]:
    """Normalize module record fields for markdown output."""
    module_name = first_non_empty_string(record, ["module", "module_name", "name", "id"])
    location = first_non_empty_string(record, ["location", "path", "file", "module_path"])

    classes = extract_name_list(record.get("classes"))
    functions = extract_name_list(record.get("functions"))

    if not module_name:
        module_name = f"module_{fallback_index}"

    if not location:
        location = "(not provided)"

    return {
        "module_name": module_name,
        "location": location,
        "classes": sorted(set(classes), key=str.lower),
        "functions": sorted(set(functions), key=str.lower),
    }


def format_list(items: list[str]) -> str:
    """Format list entries for markdown block content."""
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def render_markdown(modules: list[dict[str, Any]], input_path: Path) -> str:
    """Render module summary markdown."""
    lines: list[str] = []
    lines.append("# Module Summary")
    lines.append("")
    lines.append(f"Source: {input_path.as_posix()}")
    lines.append(f"Generated At: {utc_now_iso()}")
    lines.append("")

    if not modules:
        lines.append("No modules discovered in module_index.json.")
        lines.append("")
        return "\n".join(lines)

    for module in modules:
        lines.append(f"## {module['module_name']}")
        lines.append("")
        lines.append(f"- Module Name: {module['module_name']}")
        lines.append(f"- Location: {module['location']}")
        lines.append("- Classes:")
        lines.append(format_list(module["classes"]))
        lines.append("- Functions:")
        lines.append(format_list(module["functions"]))
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Generate module summary from module_index.json")
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=generated_dir(),
        help="Directory containing module_index.json and module_summary.md",
    )
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    generated_dir = args.generated_dir.resolve()

    if not generated_dir.exists() or not generated_dir.is_dir():
        raise SystemExit(f"Invalid --generated-dir: {generated_dir}")

    input_path = generated_dir / INPUT_FILE
    if not input_path.exists() or not input_path.is_file():
        raise SystemExit(f"Missing input file: {input_path}")

    payload = load_json(input_path)
    discovered = discover_module_records(payload)

    modules = [
        normalize_module_record(record, idx)
        for idx, record in enumerate(discovered, start=1)
    ]

    modules.sort(key=lambda item: item["module_name"].lower())

    markdown = render_markdown(modules, input_path)
    output_path = generated_dir / OUTPUT_FILE
    write_text(output_path, markdown)


if __name__ == "__main__":
    main()
