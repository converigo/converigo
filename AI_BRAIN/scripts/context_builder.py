#!/usr/bin/env python3
"""Build primary AI context from generated metadata files."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import generated_dir, load_json, write_json


def utc_now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def summarize_project_index(payload: Any) -> dict[str, Any]:
    """Summarize project index payload into metadata counts."""
    if not isinstance(payload, list):
        return {"status": "invalid", "note": "project_index.json must be a list"}

    extension_counts: Counter[str] = Counter()
    for item in payload:
        if isinstance(item, dict) and isinstance(item.get("extension"), str):
            extension_counts[item["extension"].lower()] += 1

    return {
        "status": "ok",
        "files": len(payload),
        "extension_counts": dict(sorted(extension_counts.items())),
    }


def status_block(name: str, payload: Any) -> dict[str, Any]:
    """Create a generic metadata status block for a JSON payload."""
    if isinstance(payload, list):
        return {
            "status": "ok",
            "container": "list",
            "records": len(payload),
            "name": name,
        }

    if isinstance(payload, dict):
        return {
            "status": "ok",
            "container": "dict",
            "top_level_keys": sorted(payload.keys()),
            "name": name,
        }

    return {
        "status": "invalid",
        "container": type(payload).__name__,
        "name": name,
    }


def read_generated_jsons(directory: Path) -> dict[str, Any]:
    """Read every JSON file under generated directory."""
    payloads: dict[str, Any] = {}

    for path in sorted(directory.glob("*.json"), key=lambda p: p.name.lower()):
        try:
            payloads[path.name] = load_json(path)
        except Exception as exc:  # noqa: BLE001
            payloads[path.name] = {"_read_error": str(exc)}

    return payloads


def build_context(generated: Path) -> dict[str, Any]:
    """Build consolidated primary AI context from all generated metadata files."""
    payloads = read_generated_jsons(generated)

    project_index = payloads.get("project_index.json")
    project_map = payloads.get("project_map.json")
    module_index = payloads.get("module_index.json")
    routes = payloads.get("routes.json")
    services = payloads.get("services.json")
    converters = payloads.get("converters.json")
    imports = payloads.get("import_map.json")

    overview = {
        "generated_at": utc_now_iso(),
        "generated_files_loaded": len(payloads),
        "available_generated_files": sorted(payloads.keys()),
    }

    context = {
        "project_overview": summarize_project_index(project_index),
        "folder_map": status_block("project_map", project_map),
        "modules": status_block("module_index", module_index),
        "services": status_block("services", services),
        "routes": status_block("routes", routes),
        "converters": status_block("converters", converters),
        "imports": status_block("import_map", imports),
    }

    # Include direct metadata payloads so context remains source-grounded.
    context_payload = {
        "project_map": project_map,
        "module_index": module_index,
        "services": services,
        "routes": routes,
        "converters": converters,
        "import_map": imports,
    }

    return {
        "overview": overview,
        "context": context,
        "metadata": context_payload,
        "all_generated_payloads": payloads,
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Build primary AI context from generated metadata files")
    parser.add_argument("--generated-dir", type=Path, default=generated_dir(), help="Generated metadata dir")
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    generated = args.generated_dir.resolve()

    if not generated.exists() or not generated.is_dir():
        raise SystemExit(f"Invalid --generated-dir: {generated}")

    context = build_context(generated)
    write_json(generated / "context.json", context)


if __name__ == "__main__":
    main()
