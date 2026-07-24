#!/usr/bin/env python3
"""Associate modules, services, and converters with markdown documentation files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain_common import get_brain_paths, is_non_empty_str, stem_from_path, tokenize, write_json
from brain_common import read_generated_json


@dataclass(frozen=True)
class DocumentationMapping:
    entity_type: str
    entity_name: str
    source_file: str
    docs: list[str]


def markdown_files(project_index_payload: Any) -> list[str]:
    """Collect markdown file paths from project index."""
    if not isinstance(project_index_payload, list):
        return []

    docs: list[str] = []
    for item in project_index_payload:
        if isinstance(item, dict) and is_non_empty_str(item.get("path")) and item.get("extension") == ".md":
            docs.append(str(item["path"]))

    return sorted(set(docs))


def doc_matches(tokens: set[str], docs: list[str]) -> list[str]:
    """Match docs using filename token overlap."""
    matches: list[str] = []

    for doc_path in docs:
        doc_tokens = tokenize(stem_from_path(doc_path))
        if tokens.intersection(doc_tokens):
            matches.append(doc_path)

    return sorted(set(matches))


def module_mappings(project_index_payload: Any, docs: list[str]) -> list[DocumentationMapping]:
    """Create module-to-doc mappings."""
    mappings: list[DocumentationMapping] = []
    if not isinstance(project_index_payload, list):
        return mappings

    for item in project_index_payload:
        if not isinstance(item, dict):
            continue
        source = item.get("path")
        extension = item.get("extension")
        if not (is_non_empty_str(source) and extension == ".py"):
            continue

        source_path = str(source)
        tokens = tokenize(stem_from_path(source_path))
        mappings.append(
            DocumentationMapping(
                entity_type="module",
                entity_name=stem_from_path(source_path),
                source_file=source_path,
                docs=doc_matches(tokens, docs),
            )
        )

    mappings.sort(key=lambda item: item.source_file)
    return mappings


def service_mappings(services_payload: Any, docs: list[str]) -> list[DocumentationMapping]:
    """Create service-to-doc mappings."""
    mappings: list[DocumentationMapping] = []
    if not (isinstance(services_payload, dict) and isinstance(services_payload.get("services"), list)):
        return mappings

    for item in services_payload["services"]:
        if not isinstance(item, dict):
            continue
        name = item.get("service_name")
        source = item.get("source_file")
        if not (is_non_empty_str(name) and is_non_empty_str(source)):
            continue

        tokens = tokenize(str(name)).union(tokenize(stem_from_path(str(source))))
        mappings.append(
            DocumentationMapping(
                entity_type="service",
                entity_name=str(name),
                source_file=str(source),
                docs=doc_matches(tokens, docs),
            )
        )

    mappings.sort(key=lambda item: item.entity_name.lower())
    return mappings


def converter_mappings(converters_payload: Any, docs: list[str]) -> list[DocumentationMapping]:
    """Create converter-to-doc mappings."""
    mappings: list[DocumentationMapping] = []
    if not (isinstance(converters_payload, dict) and isinstance(converters_payload.get("converters"), list)):
        return mappings

    for item in converters_payload["converters"]:
        if not isinstance(item, dict):
            continue
        name = item.get("converter_name")
        source = item.get("source_file")
        if not (is_non_empty_str(name) and is_non_empty_str(source)):
            continue

        tokens = tokenize(str(name)).union(tokenize(stem_from_path(str(source))))
        mappings.append(
            DocumentationMapping(
                entity_type="converter",
                entity_name=str(name),
                source_file=str(source),
                docs=doc_matches(tokens, docs),
            )
        )

    mappings.sort(key=lambda item: (item.entity_name.lower(), item.source_file))
    return mappings


def main() -> None:
    """Program entry point."""
    paths = get_brain_paths()
    project_index = read_generated_json(paths.generated_dir, "project_index.json")
    services = read_generated_json(paths.generated_dir, "services.json")
    converters = read_generated_json(paths.generated_dir, "converters.json")

    docs = markdown_files(project_index.data)
    payload = {
        "inputs": {
            "project_index": project_index.error or "ok",
            "services": services.error or "ok",
            "converters": converters.error or "ok",
        },
        "totals": {
            "markdown_files": len(docs),
        },
        "documentation_files": docs,
        "modules": [item.__dict__ for item in module_mappings(project_index.data, docs)],
        "services": [item.__dict__ for item in service_mappings(services.data, docs)],
        "converters": [item.__dict__ for item in converter_mappings(converters.data, docs)],
    }

    write_json(paths.generated_dir / "documentation_map.json", payload)


if __name__ == "__main__":
    main()
