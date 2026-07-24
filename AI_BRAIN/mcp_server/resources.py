#!/usr/bin/env python3
"""Resource definitions for AI_BRAIN MCP Server."""

from __future__ import annotations

from pathlib import Path
from typing import Any


RESOURCE_FILES = [
    "semantic_knowledge.json",
    "relationships.json",
    "dependency_graph.json",
    "reasoning_context.json",
]


def generated_dir() -> Path:
    """Return the generated metadata directory for AI_BRAIN."""
    return Path(__file__).resolve().parent.parent / "generated"


def get_resource_path(resource_name: str) -> Path:
    """Return the path to a named resource file."""
    return generated_dir() / resource_name


def load_resource(resource_name: str) -> dict[str, Any]:
    """Load a JSON resource from generated metadata."""
    path = get_resource_path(resource_name)
    if not path.exists() or not path.is_file():
        return {}
    try:
        import json

        with path.open("r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}
