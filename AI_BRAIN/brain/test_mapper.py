#!/usr/bin/env python3
"""Map modules, services, and converters to test files using filename matching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain_common import get_brain_paths, is_non_empty_str, stem_from_path, tokenize, write_json
from brain_common import read_generated_json


@dataclass(frozen=True)
class MappingRecord:
    entity_type: str
    entity_name: str
    source_file: str
    matched_tests: list[str]


def discover_test_files(project_index_payload: Any) -> list[str]:
    """Collect test file paths from project index metadata."""
    if not isinstance(project_index_payload, list):
        return []

    tests: list[str] = []
    for item in project_index_payload:
        if not isinstance(item, dict):
            continue
        path_value = item.get("path")
        extension = item.get("extension")
        if is_non_empty_str(path_value) and extension == ".py":
            normalized = str(path_value)
            filename = Path(normalized).name.lower()
            if normalized.startswith("tests/") or filename.startswith("test_"):
                tests.append(normalized)

    return sorted(set(tests))


def match_tests(entity_tokens: set[str], test_files: list[str]) -> list[str]:
    """Match test files by filename token overlap."""
    matches: list[str] = []

    for test_path in test_files:
        test_stem_tokens = tokenize(stem_from_path(test_path))
        if entity_tokens.intersection(test_stem_tokens):
            matches.append(test_path)

    return sorted(set(matches))


def service_records(services_payload: Any, test_files: list[str]) -> list[MappingRecord]:
    """Build service-to-test mappings."""
    records: list[MappingRecord] = []

    if not (isinstance(services_payload, dict) and isinstance(services_payload.get("services"), list)):
        return records

    for item in services_payload["services"]:
        if not isinstance(item, dict):
            continue
        name = item.get("service_name")
        source = item.get("source_file")
        if not (is_non_empty_str(name) and is_non_empty_str(source)):
            continue

        tokens = tokenize(str(name)).union(tokenize(stem_from_path(str(source))))
        records.append(
            MappingRecord(
                entity_type="service",
                entity_name=str(name),
                source_file=str(source),
                matched_tests=match_tests(tokens, test_files),
            )
        )

    return records


def converter_records(converters_payload: Any, test_files: list[str]) -> list[MappingRecord]:
    """Build converter-to-test mappings."""
    records: list[MappingRecord] = []

    if not (isinstance(converters_payload, dict) and isinstance(converters_payload.get("converters"), list)):
        return records

    for item in converters_payload["converters"]:
        if not isinstance(item, dict):
            continue
        name = item.get("converter_name")
        source = item.get("source_file")
        if not (is_non_empty_str(name) and is_non_empty_str(source)):
            continue

        tokens = tokenize(str(name)).union(tokenize(stem_from_path(str(source))))
        records.append(
            MappingRecord(
                entity_type="converter",
                entity_name=str(name),
                source_file=str(source),
                matched_tests=match_tests(tokens, test_files),
            )
        )

    return records


def module_records(project_index_payload: Any, test_files: list[str]) -> list[MappingRecord]:
    """Build module-to-test mappings for Python modules."""
    records: list[MappingRecord] = []

    if not isinstance(project_index_payload, list):
        return records

    for item in project_index_payload:
        if not isinstance(item, dict):
            continue
        path_value = item.get("path")
        extension = item.get("extension")
        if not (is_non_empty_str(path_value) and extension == ".py"):
            continue

        source = str(path_value)
        if source.startswith("tests/"):
            continue

        stem_tokens = tokenize(stem_from_path(source))
        records.append(
            MappingRecord(
                entity_type="module",
                entity_name=stem_from_path(source),
                source_file=source,
                matched_tests=match_tests(stem_tokens, test_files),
            )
        )

    records.sort(key=lambda record: record.source_file)
    return records


def main() -> None:
    """Program entry point."""
    paths = get_brain_paths()
    project_index = read_generated_json(paths.generated_dir, "project_index.json")
    services = read_generated_json(paths.generated_dir, "services.json")
    converters = read_generated_json(paths.generated_dir, "converters.json")

    tests = discover_test_files(project_index.data)
    service_map = service_records(services.data, tests)
    converter_map = converter_records(converters.data, tests)
    module_map = module_records(project_index.data, tests)

    payload = {
        "inputs": {
            "project_index": project_index.error or "ok",
            "services": services.error or "ok",
            "converters": converters.error or "ok",
        },
        "totals": {
            "test_files": len(tests),
            "services_mapped": len(service_map),
            "converters_mapped": len(converter_map),
            "modules_mapped": len(module_map),
        },
        "test_files": tests,
        "services": [record.__dict__ for record in service_map],
        "converters": [record.__dict__ for record in converter_map],
        "modules": [record.__dict__ for record in module_map],
    }

    write_json(paths.generated_dir / "test_map.json", payload)


if __name__ == "__main__":
    main()
