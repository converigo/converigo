#!/usr/bin/env python3
"""Build optimized prompts for AI_BRAIN tasks using selected gateway context."""

from __future__ import annotations

from typing import Any

from .context_ranker import RankedContext
from .task_detector import detect_task_category, TaskCategory


def format_section(title: str, content: str) -> str:
    return f"{title}\n{'=' * len(title)}\n{content.strip()}\n\n"


def build_project_summary(reasoning_context: dict[str, Any]) -> str:
    architecture = reasoning_context.get("sections", {}).get("architecture", {}).get("data", {})
    totals = architecture.get("totals", {})
    categories = architecture.get("categories", {})
    backend = categories.get("Backend", {}).get("file_count", 0)
    frontend = categories.get("Frontend", {}).get("file_count", 0)
    tests = categories.get("Tests", {}).get("file_count", 0)
    docs = categories.get("Documentation", {}).get("file_count", 0)
    summary_lines = [
        f"Backend files: {backend}",
        f"Frontend files: {frontend}",
        f"Test files: {tests}",
        f"Documentation files: {docs}",
    ]
    if totals:
        summary_lines.append(f"Classified files: {totals.get('files_classified', 'unknown')}")
    return "\n".join(summary_lines)


def build_task_section(user_task: str, category: TaskCategory) -> str:
    return f"Task: {user_task}\nCategory: {category.value}"


def build_related_entries(title: str, entries: list[dict[str, Any]], key_names: list[str]) -> str:
    if not entries:
        return f"No relevant {title.lower()} found."
    lines = []
    for entry in entries[:5]:
        values = [str(entry.get(key, "")).strip() for key in key_names if entry.get(key)]
        if values:
            lines.append(" - " + " | ".join(values))
    return "\n".join(lines)


def build_dependencies_section(dependency_summary: list[dict[str, Any]]) -> str:
    if not dependency_summary:
        return "No dependency details available."
    lines = [
        f"{item['source_file']}: internal={item['internal_dependencies']}, external={item['external_dependencies']}"
        for item in dependency_summary
    ]
    return "\n".join(lines)


def build_known_risks(semantic_objects: list[dict[str, Any]]) -> str:
    risks = []
    for item in semantic_objects[:5]:
        risk = item.get("risk_level")
        if risk and risk != "low":
            risks.append(f"{item.get('module', 'unknown')}: {risk}")
    return "\n".join(risks) if risks else "No elevated risks detected."


def build_context_summary(ranked: RankedContext) -> str:
    sections = []
    sections.append(f"Modules: {len(ranked.modules)}")
    sections.append(f"Services: {len(ranked.services)}")
    sections.append(f"Routes: {len(ranked.routes)}")
    sections.append(f"Converters: {len(ranked.converters)}")
    return "\n".join(sections)


def build_prompt(
    user_task: str,
    context: dict[str, Any],
    ranked: RankedContext,
    category: TaskCategory,
) -> str:
    project_summary = build_project_summary(context.get("reasoning_context", {}))
    task_section = build_task_section(user_task, category)
    relevant_modules = build_related_entries("Relevant Modules", ranked.modules, ["module", "purpose"])
    relevant_services = build_related_entries("Related Services", ranked.services, ["service", "module"])
    relevant_routes = build_related_entries("Related Routes", ranked.routes, ["target", "source"])
    relevant_converters = build_related_entries("Related Converters", ranked.converters, ["converter", "module"])
    dependencies = build_dependencies_section(ranked.summary.get("dependency_summary", []))
    known_risks = build_known_risks(context.get("semantic_knowledge", {}).get("semantic_objects", []))
    context_summary = build_context_summary(ranked)

    prompt_parts = [
        format_section("Project Summary", project_summary),
        format_section("Task", task_section),
        format_section("Relevant Modules", relevant_modules),
        format_section("Dependencies", dependencies),
        format_section("Related Services", relevant_services),
        format_section("Related Routes", relevant_routes),
        format_section("Related Converters", relevant_converters),
        format_section("Known Risks", known_risks),
        format_section("Context", context_summary),
    ]

    rules = [
        "Use only the provided context and metadata.",
        "Do not make assumptions beyond the repository content.",
        "Focus on code, dependencies, and test coverage.",
        "Provide concise recommendations and implementation guidance.",
    ]
    prompt_parts.insert(4, format_section("Coding Rules", "\n".join(rules)))

    return "\n".join(prompt_parts).strip()
