#!/usr/bin/env python3
"""Build metadata-only relationship graph from generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain_common import (
    BrainPaths,
    get_brain_paths,
    is_non_empty_str,
    normalize_module_name,
    read_generated_json,
    stem_from_path,
    write_json,
)


@dataclass(frozen=True)
class Relationship:
    source_type: str
    source: str
    relationship: str
    target_type: str
    target: str
    evidence: str


def service_lookup(services_payload: Any) -> dict[str, str]:
    """Map service source-file module key to service name."""
    mapping: dict[str, str] = {}
    if not isinstance(services_payload, dict):
        return mapping

    items = services_payload.get("services")
    if not isinstance(items, list):
        return mapping

    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("service_name")
        source = item.get("source_file")
        if is_non_empty_str(name) and is_non_empty_str(source):
            module_key = str(source).replace("/", ".").removesuffix(".py")
            mapping[module_key] = str(name)

    return mapping


def route_lookup(routes_payload: Any) -> dict[str, list[dict[str, str]]]:
    """Group routes by source file."""
    grouped: dict[str, list[dict[str, str]]] = {}
    if not isinstance(routes_payload, dict):
        return grouped

    items = routes_payload.get("routes")
    if not isinstance(items, list):
        return grouped

    for item in items:
        if not isinstance(item, dict):
            continue
        source = item.get("source_file")
        endpoint = item.get("endpoint")
        method = item.get("http_method")
        if is_non_empty_str(source):
            grouped.setdefault(str(source), []).append(
                {
                    "endpoint": str(endpoint) if endpoint is not None else "",
                    "method": str(method) if method is not None else "",
                }
            )

    return grouped


def converter_lookup(converters_payload: Any) -> dict[str, dict[str, str]]:
    """Map converter source files to converter metadata."""
    mapping: dict[str, dict[str, str]] = {}
    if not isinstance(converters_payload, dict):
        return mapping

    items = converters_payload.get("converters")
    if not isinstance(items, list):
        return mapping

    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("converter_name")
        source = item.get("source_file")
        category = item.get("category")
        if is_non_empty_str(name) and is_non_empty_str(source):
            mapping[str(source)] = {
                "converter_name": str(name),
                "category": str(category) if category is not None else "unknown",
            }

    return mapping


def discover_module_paths(project_index_payload: Any) -> list[str]:
    """Discover module file paths from project index metadata."""
    modules: list[str] = []
    if not isinstance(project_index_payload, list):
        return modules

    for item in project_index_payload:
        if not isinstance(item, dict):
            continue
        path_value = item.get("path")
        extension = item.get("extension")
        if is_non_empty_str(path_value) and extension == ".py":
            modules.append(str(path_value))

    return sorted(set(modules))


def import_records(import_map_payload: Any) -> list[dict[str, Any]]:
    """Return import records list from import_map payload."""
    if not isinstance(import_map_payload, dict):
        return []
    imports = import_map_payload.get("imports")
    return imports if isinstance(imports, list) else []


def build_relationships(paths: BrainPaths) -> dict[str, Any]:
    """Build all required relationship categories from metadata inputs."""
    project_index = read_generated_json(paths.generated_dir, "project_index.json")
    routes = read_generated_json(paths.generated_dir, "routes.json")
    services = read_generated_json(paths.generated_dir, "services.json")
    converters = read_generated_json(paths.generated_dir, "converters.json")
    import_map = read_generated_json(paths.generated_dir, "import_map.json")

    service_by_module = service_lookup(services.data)
    routes_by_file = route_lookup(routes.data)
    converter_by_file = converter_lookup(converters.data)
    module_paths = discover_module_paths(project_index.data)
    imports = import_records(import_map.data)

    relationships: list[Relationship] = []

    module_key_lookup = {path: path.replace("/", ".").removesuffix(".py") for path in module_paths}

    for module_path in module_paths:
        if module_path in routes_by_file:
            for route_info in routes_by_file[module_path]:
                target = f"{route_info['method']} {route_info['endpoint']}".strip()
                relationships.append(
                    Relationship(
                        source_type="module",
                        source=module_path,
                        relationship="module_to_router",
                        target_type="router",
                        target=target,
                        evidence="routes.source_file",
                    )
                )

    imports_by_source: dict[str, list[dict[str, Any]]] = {}
    for record in imports:
        if not isinstance(record, dict):
            continue
        source_file = record.get("source_file")
        if is_non_empty_str(source_file):
            imports_by_source.setdefault(str(source_file), []).append(record)

    for module_path in module_paths:
        source_imports = imports_by_source.get(module_path, [])
        for record in source_imports:
            module_name = normalize_module_name(record.get("module"))
            if module_name.startswith("app.services"):
                service_name = service_by_module.get(module_name)
                if service_name:
                    relationships.append(
                        Relationship(
                            source_type="module",
                            source=module_path,
                            relationship="module_to_service",
                            target_type="service",
                            target=service_name,
                            evidence="import_map.module=app.services.*",
                        )
                    )

    route_files = set(routes_by_file.keys())
    for route_file in sorted(route_files):
        for record in imports_by_source.get(route_file, []):
            module_name = normalize_module_name(record.get("module"))
            if module_name.startswith("app.services"):
                service_name = service_by_module.get(module_name)
                if service_name:
                    relationships.append(
                        Relationship(
                            source_type="router",
                            source=route_file,
                            relationship="router_to_service",
                            target_type="service",
                            target=service_name,
                            evidence="import_map.module=app.services.*",
                        )
                    )

    service_source_lookup: dict[str, str] = {}
    if isinstance(services.data, dict) and isinstance(services.data.get("services"), list):
        for item in services.data["services"]:
            if isinstance(item, dict) and is_non_empty_str(item.get("service_name")) and is_non_empty_str(item.get("source_file")):
                service_source_lookup[str(item["service_name"])] = str(item["source_file"])

    for service_name, service_file in sorted(service_source_lookup.items()):
        for record in imports_by_source.get(service_file, []):
            module_name = normalize_module_name(record.get("module"))
            if module_name.startswith("app.plugins"):
                imported_name = record.get("import_name")
                if is_non_empty_str(imported_name):
                    relationships.append(
                        Relationship(
                            source_type="service",
                            source=service_name,
                            relationship="service_to_converter",
                            target_type="converter",
                            target=str(imported_name),
                            evidence="import_map.module=app.plugins.*",
                        )
                    )

    for source_file, converter_info in sorted(converter_by_file.items()):
        converter_name = converter_info["converter_name"]
        plugin_name = f"plugin:{converter_info['category']}/{stem_from_path(source_file)}"
        relationships.append(
            Relationship(
                source_type="converter",
                source=converter_name,
                relationship="converter_to_plugin",
                target_type="plugin",
                target=plugin_name,
                evidence="converters.category+source_file",
            )
        )

    deduped: dict[tuple[str, str, str, str, str, str], Relationship] = {}
    for relation in relationships:
        key = (
            relation.source_type,
            relation.source,
            relation.relationship,
            relation.target_type,
            relation.target,
            relation.evidence,
        )
        deduped[key] = relation

    ordered = sorted(
        deduped.values(),
        key=lambda item: (item.source_type, item.source, item.relationship, item.target_type, item.target),
    )

    return {
        "inputs": {
            "project_index": project_index.error or "ok",
            "routes": routes.error or "ok",
            "services": services.error or "ok",
            "converters": converters.error or "ok",
            "import_map": import_map.error or "ok",
        },
        "totals": {
            "module_count": len(module_paths),
            "relationship_count": len(ordered),
        },
        "relationships": [relation.__dict__ for relation in ordered],
    }


def main() -> None:
    """Program entry point."""
    paths = get_brain_paths()
    payload = build_relationships(paths)
    write_json(paths.generated_dir / "relationships.json", payload)


if __name__ == "__main__":
    main()
