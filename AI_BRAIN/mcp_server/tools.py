#!/usr/bin/env python3
"""MCP tool implementations for AI_BRAIN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .resources import RESOURCE_FILES, load_resource
from AI_BRAIN.gateway.gateway import build_prompt_for_task


@dataclass(frozen=True)
class ToolResult:
    name: str
    description: str
    data: Any


def project_summary() -> ToolResult:
    """Return a summary of the AI_BRAIN project from reasoning context."""
    reasoning = load_resource("reasoning_context.json")
    architecture = reasoning.get("sections", {}).get("architecture", {}).get("data", {})
    totals = architecture.get("totals", {})
    categories = architecture.get("categories", {})
    summary = {
        "backend_files": categories.get("Backend", {}).get("file_count", 0),
        "frontend_files": categories.get("Frontend", {}).get("file_count", 0),
        "test_files": categories.get("Tests", {}).get("file_count", 0),
        "documentation_files": categories.get("Documentation", {}).get("file_count", 0),
        "classified_files": totals.get("files_classified", 0),
    }
    return ToolResult(
        name="project_summary",
        description="Summarize repository architecture and file counts.",
        data=summary,
    )


def find_module(module_name: str) -> ToolResult:
    """Find semantic module records by name or path fragment."""
    knowledge = load_resource("semantic_knowledge.json")
    results: list[dict[str, Any]] = []
    for item in knowledge.get("semantic_objects", []):
        if not isinstance(item, dict):
            continue
        candidate = item.get("module", "")
        if module_name.lower() in candidate.lower():
            results.append(item)
    return ToolResult(
        name="find_module",
        description="Find semantic module records matching a name or fragment.",
        data={"query": module_name, "matches": results},
    )


def related_modules(module_name: str) -> ToolResult:
    """Return modules related to the given module by folder and service linkage."""
    knowledge = load_resource("semantic_knowledge.json")
    matches = []
    for item in knowledge.get("semantic_objects", []):
        if not isinstance(item, dict):
            continue
        candidate = item.get("module", "")
        if module_name.lower() in candidate.lower():
            matches.append(item)
            break

    related: list[dict[str, Any]] = []
    if matches:
        source = matches[0].get("module", "")
        related = [
            {
                "module": item.get("module"),
                "purpose": item.get("purpose"),
                "related_services": item.get("related_services", []),
                "related_routes": item.get("related_routes", []),
            }
            for item in knowledge.get("semantic_objects", [])
            if item.get("module") in matches[0].get("related_modules", [])
        ]

    return ToolResult(
        name="related_modules",
        description="Return modules that are related to a specified module.",
        data={"module": module_name, "related_modules": related},
    )


def build_context(task: str) -> ToolResult:
    """Build an optimized prompt for a user task using the gateway."""
    prompt = build_prompt_for_task(task)
    return ToolResult(
        name="build_context",
        description="Build an AI prompt for the task using AI_BRAIN generated context.",
        data={"task": task, "prompt": prompt},
    )


def available_tools() -> list[str]:
    return ["project_summary", "find_module", "related_modules", "build_context"]


def available_resources() -> list[str]:
    return list(RESOURCE_FILES)
