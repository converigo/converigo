#!/usr/bin/env python3
"""Generate semantic_knowledge.json from generated metadata artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brain_common import (
    get_brain_paths,
    is_non_empty_str,
    parent_dir_from_path,
    read_generated_json,
    stem_from_path,
    write_json,
)


@dataclass(frozen=True)
class SemanticModule:
    module: str
    category: str
    purpose: str
    related_modules: list[str]
    related_services: list[str]
    related_routes: list[str]
    related_tests: list[str]
    related_documentation: list[str]
    dependency_summary: dict[str, int]
    risk_level: str
    status: str


def module_records(project_index_payload: Any, module_index_payload: Any) -> list[dict[str, str]]:
    """Discover module records using module_index or project_index fallback."""
    records: list[dict[str, str]] = []

    if isinstance(module_index_payload, dict) and isinstance(module_index_payload.get("modules"), list):
        for item in module_index_payload["modules"]:
            if not isinstance(item, dict):
                continue
            path_value = item.get("path") or item.get("location") or item.get("source_file")
            name_value = item.get("module") or item.get("module_name") or item.get("name")
            if is_non_empty_str(path_value):
                records.append(
                    {
                        "module": str(name_value) if is_non_empty_str(name_value) else stem_from_path(str(path_value)),
                        "source_file": str(path_value),
                    }
                )

    if records:
        dedup = {(item["module"], item["source_file"]): item for item in records}
        return sorted(dedup.values(), key=lambda item: (item["source_file"], item["module"]))

    if isinstance(project_index_payload, list):
        for item in project_index_payload:
            if isinstance(item, dict) and is_non_empty_str(item.get("path")) and item.get("extension") == ".py":
                path_value = str(item["path"])
                records.append({"module": stem_from_path(path_value), "source_file": path_value})

    dedup = {(item["module"], item["source_file"]): item for item in records}
    return sorted(dedup.values(), key=lambda item: (item["source_file"], item["module"]))


def infer_category(source_file: str) -> str:
    """Infer module category from path only."""
    normalized = source_file.lower()
    if "/services/" in f"/{normalized}/":
        return "service"
    if "/routers/" in f"/{normalized}/":
        return "router"
    if "/plugins/" in f"/{normalized}/":
        return "plugin"
    if normalized.startswith("tests/"):
        return "test"
    if "/templates/" in f"/{normalized}/":
        return "template"
    if normalized.startswith("AI_BRAIN/") or normalized.startswith("ai_brain/"):
        return "ai_infrastructure"
    return "module"


def infer_purpose(category: str) -> str:
    """Derive purpose from category only."""
    mapping = {
        "service": "service metadata module",
        "router": "router metadata module",
        "plugin": "plugin metadata module",
        "test": "test metadata module",
        "template": "template-related module",
        "ai_infrastructure": "ai infrastructure module",
        "module": "general module",
    }
    return mapping.get(category, "general module")


def map_relationships_by_module(relationships_payload: Any) -> dict[str, dict[str, list[str]]]:
    """Index relationship records by module source path."""
    index: dict[str, dict[str, list[str]]] = {}

    if not (isinstance(relationships_payload, dict) and isinstance(relationships_payload.get("relationships"), list)):
        return index

    for rel in relationships_payload["relationships"]:
        if not isinstance(rel, dict):
            continue

        source_type = rel.get("source_type")
        source = rel.get("source")
        relation = rel.get("relationship")
        target = rel.get("target")

        if not (is_non_empty_str(source_type) and is_non_empty_str(source) and is_non_empty_str(relation)):
            continue

        module_key = str(source)
        bucket = index.setdefault(module_key, {"services": [], "routes": [], "converters": []})

        if relation == "module_to_service" and is_non_empty_str(target):
            bucket["services"].append(str(target))
        if relation == "module_to_router" and is_non_empty_str(target):
            bucket["routes"].append(str(target))

    for key in list(index.keys()):
        index[key]["services"] = sorted(set(index[key]["services"]))
        index[key]["routes"] = sorted(set(index[key]["routes"]))
        index[key]["converters"] = sorted(set(index[key]["converters"]))

    return index


def dependency_index(dependency_payload: Any) -> dict[str, dict[str, int]]:
    """Build dependency count summaries by source file."""
    index: dict[str, dict[str, int]] = {}

    by_source = dependency_payload.get("by_source") if isinstance(dependency_payload, dict) else None
    if isinstance(by_source, dict):
        for source, counts in by_source.items():
            if isinstance(counts, dict):
                index[str(source)] = {
                    "internal": int(counts.get("internal", 0)),
                    "external": int(counts.get("external", 0)),
                }

    return index


def test_index(test_map_payload: Any) -> dict[str, list[str]]:
    """Index module file to matched tests."""
    index: dict[str, list[str]] = {}
    if not (isinstance(test_map_payload, dict) and isinstance(test_map_payload.get("modules"), list)):
        return index

    for item in test_map_payload["modules"]:
        if not isinstance(item, dict):
            continue
        source = item.get("source_file")
        matches = item.get("matched_tests")
        if is_non_empty_str(source) and isinstance(matches, list):
            index[str(source)] = [str(test) for test in matches if is_non_empty_str(test)]

    return index


def docs_index(documentation_payload: Any) -> dict[str, list[str]]:
    """Index module file to matched docs."""
    index: dict[str, list[str]] = {}
    if not (isinstance(documentation_payload, dict) and isinstance(documentation_payload.get("modules"), list)):
        return index

    for item in documentation_payload["modules"]:
        if not isinstance(item, dict):
            continue
        source = item.get("source_file")
        docs = item.get("docs")
        if is_non_empty_str(source) and isinstance(docs, list):
            index[str(source)] = [str(doc) for doc in docs if is_non_empty_str(doc)]

    return index


def related_modules_by_folder(records: list[dict[str, str]]) -> dict[str, list[str]]:
    """Relate modules by parent folder metadata."""
    folder_members: dict[str, list[str]] = {}
    for record in records:
        folder = parent_dir_from_path(record["source_file"])
        folder_members.setdefault(folder, []).append(record["source_file"])

    output: dict[str, list[str]] = {}
    for members in folder_members.values():
        unique_sorted = sorted(set(members))
        for source in unique_sorted:
            output[source] = [item for item in unique_sorted if item != source]

    return output


def infer_risk(category: str, dependency_summary: dict[str, int], route_count: int, service_count: int) -> str:
    """Infer risk level using metadata exposure and dependency volume."""
    external = dependency_summary.get("external", 0)
    internal = dependency_summary.get("internal", 0)

    if category == "router" or route_count > 0:
        if external >= 5:
            return "high"
        return "medium"

    if category == "service" or service_count > 0:
        if external >= 8 or internal >= 12:
            return "high"
        if external >= 3 or internal >= 6:
            return "medium"
        return "low"

    if external >= 10:
        return "medium"
    return "low"


def infer_status(related_services: list[str], related_routes: list[str], dependency_summary: dict[str, int]) -> str:
    """Infer semantic status from linkage completeness."""
    if related_services or related_routes:
        return "linked"
    if dependency_summary.get("internal", 0) > 0 or dependency_summary.get("external", 0) > 0:
        return "observed"
    return "isolated"


def build_semantic_knowledge() -> dict[str, Any]:
    """Build semantic knowledge objects from generated metadata artifacts."""
    paths = get_brain_paths()

    project_index = read_generated_json(paths.generated_dir, "project_index.json")
    module_index = read_generated_json(paths.generated_dir, "module_index.json")
    relationships = read_generated_json(paths.generated_dir, "relationships.json")
    dependency = read_generated_json(paths.generated_dir, "dependency_graph.json")
    test_map = read_generated_json(paths.generated_dir, "test_map.json")
    documentation = read_generated_json(paths.generated_dir, "documentation_map.json")

    modules = module_records(project_index.data, module_index.data)
    rel_index = map_relationships_by_module(relationships.data)
    dep_index = dependency_index(dependency.data)
    tests = test_index(test_map.data)
    docs = docs_index(documentation.data)
    module_neighbors = related_modules_by_folder(modules)

    semantic_objects: list[SemanticModule] = []

    for record in modules:
        source_file = record["source_file"]
        category = infer_category(source_file)
        relation_bucket = rel_index.get(source_file, {"services": [], "routes": [], "converters": []})
        dependency_summary = dep_index.get(source_file, {"internal": 0, "external": 0})
        related_services = sorted(set(relation_bucket.get("services", [])))
        related_routes = sorted(set(relation_bucket.get("routes", [])))

        semantic = SemanticModule(
            module=source_file,
            category=category,
            purpose=infer_purpose(category),
            related_modules=module_neighbors.get(source_file, []),
            related_services=related_services,
            related_routes=related_routes,
            related_tests=sorted(set(tests.get(source_file, []))),
            related_documentation=sorted(set(docs.get(source_file, []))),
            dependency_summary=dependency_summary,
            risk_level=infer_risk(category, dependency_summary, len(related_routes), len(related_services)),
            status=infer_status(related_services, related_routes, dependency_summary),
        )
        semantic_objects.append(semantic)

    semantic_objects.sort(key=lambda item: item.module)

    return {
        "inputs": {
            "project_index": project_index.error or "ok",
            "module_index": module_index.error or "ok",
            "relationships": relationships.error or "ok",
            "dependency_graph": dependency.error or "ok",
            "test_map": test_map.error or "ok",
            "documentation_map": documentation.error or "ok",
        },
        "totals": {
            "modules": len(semantic_objects),
            "linked_modules": sum(1 for item in semantic_objects if item.status == "linked"),
        },
        "semantic_objects": [item.__dict__ for item in semantic_objects],
    }


def main() -> None:
    """Program entry point."""
    paths = get_brain_paths()
    payload = build_semantic_knowledge()
    write_json(paths.generated_dir / "semantic_knowledge.json", payload)


if __name__ == "__main__":
    main()
