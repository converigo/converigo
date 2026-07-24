#!/usr/bin/env python3
"""Build internal/external dependency metadata from import_map.json."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from brain_common import get_brain_paths, is_non_empty_str, read_generated_json, write_json

INTERNAL_PREFIXES = ("app", "AI_BRAIN", "tests", ".")


@dataclass(frozen=True)
class DependencyRecord:
    source_file: str
    dependency: str
    import_type: str
    dependency_scope: str


def classify_dependency(module_name: str) -> str:
    """Classify dependency scope based on module prefix."""
    for prefix in INTERNAL_PREFIXES:
        if module_name.startswith(prefix):
            return "internal"
    return "external"


def build_dependency_graph(import_map_payload: Any) -> dict[str, Any]:
    """Transform import_map records into dependency graph metadata."""
    imports = []
    if isinstance(import_map_payload, dict) and isinstance(import_map_payload.get("imports"), list):
        imports = import_map_payload["imports"]

    records: list[DependencyRecord] = []

    for item in imports:
        if not isinstance(item, dict):
            continue

        source_file = item.get("source_file")
        module_name = item.get("module")
        import_type = item.get("type")

        if not (is_non_empty_str(source_file) and is_non_empty_str(module_name) and is_non_empty_str(import_type)):
            continue

        scope = classify_dependency(str(module_name))
        records.append(
            DependencyRecord(
                source_file=str(source_file),
                dependency=str(module_name),
                import_type=str(import_type),
                dependency_scope=scope,
            )
        )

    deduped = {
        (record.source_file, record.dependency, record.import_type, record.dependency_scope): record
        for record in records
    }

    ordered = sorted(
        deduped.values(),
        key=lambda item: (item.dependency_scope, item.source_file, item.dependency, item.import_type),
    )

    internal = [record.__dict__ for record in ordered if record.dependency_scope == "internal"]
    external = [record.__dict__ for record in ordered if record.dependency_scope == "external"]

    by_source: dict[str, dict[str, int]] = {}
    for record in ordered:
        bucket = by_source.setdefault(record.source_file, {"internal": 0, "external": 0})
        bucket[record.dependency_scope] += 1

    return {
        "totals": {
            "imports_processed": len(ordered),
            "internal_dependencies": len(internal),
            "external_dependencies": len(external),
            "source_files": len(by_source),
        },
        "by_source": by_source,
        "internal_dependencies": internal,
        "external_dependencies": external,
    }


def main() -> None:
    """Program entry point."""
    paths = get_brain_paths()
    import_map = read_generated_json(paths.generated_dir, "import_map.json")

    payload = {
        "input_status": import_map.error or "ok",
        **build_dependency_graph(import_map.data),
    }

    write_json(paths.generated_dir / "dependency_graph.json", payload)


if __name__ == "__main__":
    main()
