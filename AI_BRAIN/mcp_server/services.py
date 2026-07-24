#!/usr/bin/env python3
"""Business logic services for AI_BRAIN MCP tools."""

from __future__ import annotations

from typing import Any

from .resources import load_resource


class RepositorySearchService:
    def __init__(self) -> None:
        self.file_tree = load_resource("file_tree.json")
        self.semantic_objects = load_resource("semantic_knowledge.json").get("semantic_objects", [])
        self.documentation_files = load_resource("documentation_map.json").get("documentation_files", [])

    def _collect_file_paths(self, node: dict[str, Any]) -> list[str]:
        paths: list[str] = []
        if node.get("type") == "file":
            paths.append(node.get("path", ""))
        for child in node.get("children", []):
            if isinstance(child, dict):
                paths.extend(self._collect_file_paths(child))
        return paths

    def search_repository(self, query: str, category: str | None = None, limit: int = 10) -> dict[str, Any]:
        normalized = query.strip().lower()
        if not normalized:
            return {"query": query, "category": category, "total_matches": 0, "matches": []}

        matches: dict[str, dict[str, Any]] = {}

        for path in self._collect_file_paths(self.file_tree):
            if normalized in path.lower():
                match = {
                    "path": path,
                    "category": "file",
                    "summary": "Repository file matching the query.",
                    "source": "file_tree",
                }
                matches[path] = match

        for doc_path in self.documentation_files:
            if normalized in doc_path.lower():
                match = {
                    "path": doc_path,
                    "category": "documentation",
                    "summary": "Documentation file matching the query.",
                    "source": "documentation_map",
                }
                matches[doc_path] = match

        for item in self.semantic_objects:
            module = item.get("module", "")
            purpose = item.get("purpose", "")
            if normalized in module.lower() or normalized in purpose.lower():
                match = {
                    "path": module,
                    "category": item.get("category", "module"),
                    "summary": purpose,
                    "source": "semantic_knowledge",
                }
                matches[module] = match

        filtered = list(matches.values())
        if category:
            category_lower = category.lower()
            filtered = [item for item in filtered if item["category"].lower() == category_lower]

        return {
            "query": query,
            "category": category,
            "total_matches": len(filtered),
            "matches": filtered[:limit],
        }


class ConverterRegistryService:
    def __init__(self) -> None:
        self.converters = load_resource("converters.json").get("converters", [])

    def find_converter(self, name: str) -> dict[str, Any]:
        normalized = name.strip().lower()
        matches = [
            converter
            for converter in self.converters
            if normalized in converter.get("converter_name", "").lower()
            or normalized in converter.get("source_file", "").lower()
        ]
        return {
            "query": name,
            "total_matches": len(matches),
            "matches": matches,
        }


class RouteRegistryService:
    def __init__(self) -> None:
        self.routes = load_resource("routes.json").get("routes", [])

    def find_route(self, name: str) -> dict[str, Any]:
        normalized = name.strip().lower()
        matches = [
            route
            for route in self.routes
            if normalized in route.get("endpoint", "").lower()
            or normalized in route.get("router", "").lower()
            or normalized in route.get("source_file", "").lower()
        ]
        return {
            "query": name,
            "total_matches": len(matches),
            "matches": matches,
        }


class ServiceRegistryService:
    def __init__(self) -> None:
        self.services = load_resource("services.json").get("services", [])

    def find_service(self, name: str) -> dict[str, Any]:
        normalized = name.strip().lower()
        matches = [
            service
            for service in self.services
            if normalized in service.get("service_name", "").lower()
            or normalized in service.get("source_file", "").lower()
        ]
        return {
            "query": name,
            "total_matches": len(matches),
            "matches": matches,
        }


class ArchitectureService:
    def __init__(self) -> None:
        self.reasoning_context = load_resource("reasoning_context.json")
        self.project_map = load_resource("project_map.json")

    def architecture_summary(self, detail_level: str = "summary") -> dict[str, Any]:
        architecture = self.reasoning_context.get("sections", {}).get("architecture", {}).get("data", {})

        if not architecture:
            categories = self.project_map.get("categories", {})
            totals = self.project_map.get("totals", {})
            architecture = {"categories": categories, "totals": totals}

        result: dict[str, Any] = {
            "detail_level": detail_level,
            "totals": architecture.get("totals", {}),
            "categories": architecture.get("categories", {}),
        }
        if detail_level.lower() != "summary":
            result["architecture"] = architecture
        return result


class ImplementationPlanService:
    def __init__(self) -> None:
        self.semantic_objects = load_resource("semantic_knowledge.json").get("semantic_objects", [])
        self.routes = load_resource("routes.json").get("routes", [])
        self.services = load_resource("services.json").get("services", [])

    def implementation_plan(self, task: str, focus_module: str | None = None) -> dict[str, Any]:
        normalized = task.strip().lower()
        relevant_modules: list[str] = []

        if focus_module:
            relevant_modules.append(focus_module)

        for item in self.semantic_objects:
            module = item.get("module", "")
            purpose = item.get("purpose", "")
            if normalized in module.lower() or normalized in purpose.lower():
                if module not in relevant_modules:
                    relevant_modules.append(module)
            if len(relevant_modules) >= 5:
                break

        if not relevant_modules:
            relevant_modules = [item.get("module", "") for item in self.semantic_objects[:3] if item.get("module")]

        steps = [
            {"step": "Review relevant repository metadata.", "details": "Inspect the identified modules and their dependencies before making changes."},
            {"step": "Locate impacted modules.", "details": f"Focus on: {', '.join(relevant_modules[:3])}."},
            {"step": "Update implementation and tests.", "details": "Change code in the relevant modules and add coverage for affected behavior."},
            {"step": "Validate with existing routes and services.", "details": "Confirm that related routes and services are not broken by the change."},
        ]

        references = {
            "modules": relevant_modules,
            "routes": [route.get("endpoint") for route in self.routes[:3]],
            "services": [service.get("service_name") for service in self.services[:3]],
        }

        return {
            "task": task,
            "focus_module": focus_module,
            "steps": steps,
            "references": references,
        }
