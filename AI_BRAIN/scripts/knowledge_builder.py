#!/usr/bin/env python3
"""Build metadata-only AI knowledge summary from generated project metadata.

Inputs (expected under AI_BRAIN/generated):
- project_index.json
- module_index.json
- routes.json
- services.json
- converters.json

Output:
- knowledge_summary.json

This script reads only JSON metadata files and produces aggregated summaries.
It does not read or parse source code files.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import generated_dir, load_json, write_json

INPUT_FILES = {
    "project_index": "project_index.json",
    "module_index": "module_index.json",
    "routes": "routes.json",
    "services": "services.json",
    "converters": "converters.json",
}

OUTPUT_FILE = "knowledge_summary.json"


def utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def summarize_sequence(items: list[Any]) -> dict[str, Any]:
    """Summarize a list of records without copying record content."""
    item_type_counts: Counter[str] = Counter(type(item).__name__ for item in items)

    key_counts: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    path_like_fields = 0
    sized_fields = 0

    for item in items:
        if isinstance(item, dict):
            key_counts.update(item.keys())

            if "extension" in item and isinstance(item["extension"], str):
                extension = item["extension"].strip().lower()
                extension_counts[extension] += 1

            if "path" in item and isinstance(item["path"], str):
                path_like_fields += 1

            if "size" in item and isinstance(item["size"], int):
                sized_fields += 1

    return {
        "container_type": "list",
        "record_count": len(items),
        "record_type_counts": dict(sorted(item_type_counts.items())),
        "keys_present": sorted(key_counts.keys()),
        "key_presence_count": dict(sorted(key_counts.items())),
        "path_field_count": path_like_fields,
        "size_field_count": sized_fields,
        "extension_counts": dict(sorted(extension_counts.items())),
    }


def summarize_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Summarize a mapping without copying nested values."""
    value_type_counts: Counter[str] = Counter(type(value).__name__ for value in data.values())

    top_level_keys = sorted(data.keys())

    return {
        "container_type": "dict",
        "top_level_key_count": len(top_level_keys),
        "top_level_keys": top_level_keys,
        "value_type_counts": dict(sorted(value_type_counts.items())),
    }


def summarize_json_data(data: Any) -> dict[str, Any]:
    """Create metadata summary for arbitrary JSON payload."""
    if isinstance(data, list):
        return summarize_sequence(data)
    if isinstance(data, dict):
        return summarize_mapping(data)

    return {
        "container_type": type(data).__name__,
        "note": "Unsupported top-level JSON type for detailed summary.",
    }


def file_summary(path: Path) -> dict[str, Any]:
    """Return summary for a single input JSON file."""
    if not path.exists():
        return {
            "status": "missing",
            "path": path.as_posix(),
        }

    if not path.is_file():
        return {
            "status": "invalid",
            "path": path.as_posix(),
            "reason": "Path exists but is not a file.",
        }

    try:
        payload = load_json(path)
    except json.JSONDecodeError as exc:
        return {
            "status": "invalid_json",
            "path": path.as_posix(),
            "error": str(exc),
        }

    summary = summarize_json_data(payload)

    return {
        "status": "ok",
        "path": path.as_posix(),
        "file_size_bytes": path.stat().st_size,
        "summary": summary,
    }


def build_knowledge_summary(generated_dir: Path) -> dict[str, Any]:
    """Build consolidated metadata-only summary across known generated inputs."""
    inputs: dict[str, Any] = {}

    for logical_name, filename in INPUT_FILES.items():
        input_path = generated_dir / filename
        inputs[logical_name] = file_summary(input_path)

    status_counts: Counter[str] = Counter(
        entry.get("status", "unknown") for entry in inputs.values() if isinstance(entry, dict)
    )

    return {
        "generated_at": utc_now_iso(),
        "source_directory": generated_dir.as_posix(),
        "inputs": inputs,
        "totals": {
            "input_files_expected": len(INPUT_FILES),
            "input_files_by_status": dict(sorted(status_counts.items())),
        },
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate metadata-only AI knowledge summaries from generated JSON inputs."
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=generated_dir(),
        help="Directory containing generated JSON inputs and output.",
    )
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    generated_dir = args.generated_dir.resolve()

    if not generated_dir.exists() or not generated_dir.is_dir():
        raise SystemExit(f"Invalid --generated-dir: {generated_dir}")

    knowledge_summary = build_knowledge_summary(generated_dir)
    output_path = generated_dir / OUTPUT_FILE
    write_json(output_path, knowledge_summary)


if __name__ == "__main__":
    main()
