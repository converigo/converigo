#!/usr/bin/env python3
"""Detect repository structural patterns from generated metadata only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from brain_common import get_brain_paths, is_non_empty_str, read_generated_json, write_json


@dataclass(frozen=True)
class PatternResult:
    pattern: str
    detected: bool
    evidence: dict[str, Any]


def file_paths_from_project_index(project_index_payload: Any) -> list[str]:
    """Extract file paths from project index payload."""
    if not isinstance(project_index_payload, list):
        return []

    paths: list[str] = []
    for item in project_index_payload:
        if isinstance(item, dict) and is_non_empty_str(item.get("path")):
            paths.append(str(item["path"]))

    return paths


def count_prefix(paths: list[str], prefix: str) -> int:
    """Count files that start with prefix."""
    needle = prefix.rstrip("/") + "/"
    return sum(1 for path in paths if path.startswith(needle))


def detect_patterns(project_index: Any, services: Any, routes: Any, converters: Any) -> list[PatternResult]:
    """Compute repository pattern detections based on metadata evidence."""
    paths = file_paths_from_project_index(project_index)

    services_count = 0
    if isinstance(services, dict) and isinstance(services.get("services"), list):
        services_count = len(services["services"])

    routes_count = 0
    if isinstance(routes, dict) and isinstance(routes.get("routes"), list):
        routes_count = len(routes["routes"])

    converters_count = 0
    if isinstance(converters, dict) and isinstance(converters.get("converters"), list):
        converters_count = len(converters["converters"])

    tests_count = count_prefix(paths, "tests")
    template_count = count_prefix(paths, "app/templates")

    results = [
        PatternResult(
            pattern="Service Layer",
            detected=services_count > 0,
            evidence={"services_discovered": services_count, "service_files": count_prefix(paths, "app/services")},
        ),
        PatternResult(
            pattern="Router Layer",
            detected=routes_count > 0,
            evidence={"routes_discovered": routes_count, "router_files": count_prefix(paths, "app/routers")},
        ),
        PatternResult(
            pattern="Plugin Layer",
            detected=converters_count > 0,
            evidence={"converters_discovered": converters_count, "plugin_files": count_prefix(paths, "app/plugins")},
        ),
        PatternResult(
            pattern="Template Layer",
            detected=template_count > 0,
            evidence={"template_files": template_count},
        ),
        PatternResult(
            pattern="Testing Layer",
            detected=tests_count > 0,
            evidence={"test_files": tests_count},
        ),
    ]

    return results


def main() -> None:
    """Program entry point."""
    paths = get_brain_paths()
    project_index = read_generated_json(paths.generated_dir, "project_index.json")
    services = read_generated_json(paths.generated_dir, "services.json")
    routes = read_generated_json(paths.generated_dir, "routes.json")
    converters = read_generated_json(paths.generated_dir, "converters.json")

    patterns = detect_patterns(project_index.data, services.data, routes.data, converters.data)

    payload = {
        "inputs": {
            "project_index": project_index.error or "ok",
            "services": services.error or "ok",
            "routes": routes.error or "ok",
            "converters": converters.error or "ok",
        },
        "totals": {
            "patterns_evaluated": len(patterns),
            "patterns_detected": sum(1 for pattern in patterns if pattern.detected),
        },
        "patterns": [pattern.__dict__ for pattern in patterns],
    }

    write_json(paths.generated_dir / "patterns.json", payload)


if __name__ == "__main__":
    main()
