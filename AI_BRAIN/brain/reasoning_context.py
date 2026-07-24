#!/usr/bin/env python3
"""Build consolidated reasoning context from generated semantic artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from brain_common import get_brain_paths, read_generated_json, write_json


def utc_now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def summarize_payload(payload: Any) -> dict[str, Any]:
    """Return generic payload summary for reasoning context."""
    if isinstance(payload, list):
        return {"container": "list", "records": len(payload)}
    if isinstance(payload, dict):
        return {"container": "dict", "keys": sorted(payload.keys())}
    return {"container": type(payload).__name__}


def pick_section(name: str, result_error: str | None, payload: Any) -> dict[str, Any]:
    """Construct section with status and metadata summary."""
    return {
        "name": name,
        "status": result_error or "ok",
        "summary": summarize_payload(payload),
        "data": payload,
    }


def build_reasoning_context() -> dict[str, Any]:
    """Assemble the reasoning context from all semantic-layer outputs."""
    paths = get_brain_paths()

    project_map = read_generated_json(paths.generated_dir, "project_map.json")
    services = read_generated_json(paths.generated_dir, "services.json")
    converters = read_generated_json(paths.generated_dir, "converters.json")
    routes = read_generated_json(paths.generated_dir, "routes.json")
    dependency = read_generated_json(paths.generated_dir, "dependency_graph.json")
    patterns = read_generated_json(paths.generated_dir, "patterns.json")
    knowledge = read_generated_json(paths.generated_dir, "semantic_knowledge.json")
    relationships = read_generated_json(paths.generated_dir, "relationships.json")

    sections = {
        "architecture": pick_section("architecture", project_map.error, project_map.data),
        "services": pick_section("services", services.error, services.data),
        "converters": pick_section("converters", converters.error, converters.data),
        "routers": pick_section("routers", routes.error, routes.data),
        "dependencies": pick_section("dependencies", dependency.error, dependency.data),
        "patterns": pick_section("patterns", patterns.error, patterns.data),
        "knowledge": pick_section("knowledge", knowledge.error, knowledge.data),
        "relationships": pick_section("relationships", relationships.error, relationships.data),
    }

    return {
        "generated_at": utc_now_iso(),
        "source": "AI_BRAIN/generated",
        "sections": sections,
    }


def main() -> None:
    """Program entry point."""
    paths = get_brain_paths()
    payload = build_reasoning_context()
    write_json(paths.generated_dir / "reasoning_context.json", payload)


if __name__ == "__main__":
    main()
