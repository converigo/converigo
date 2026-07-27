#!/usr/bin/env python3
"""Load AI_BRAIN generated metadata for gateway prompt construction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GatewayContext:
    context: dict[str, Any]
    semantic_knowledge: dict[str, Any]
    relationships: dict[str, Any]
    dependency_graph: dict[str, Any]
    reasoning_context: dict[str, Any]


def generated_dir() -> Path:
    """Return the AI_BRAIN/generated directory path."""
    return Path(__file__).resolve().parent.parent / "generated"


def normalize_text(value: str | None) -> str:
    """Normalize a string for token matching."""
    if not value:
        return ""
    return value.strip().lower()


def tokenize(text: str | None) -> set[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    if not text:
        return set()
    normalized = normalize_text(text)
    tokens = set()
    token = []
    for character in normalized:
        if character.isalnum():
            token.append(character)
        else:
            if token:
                tokens.add("".join(token))
                token = []
    if token:
        tokens.add("".join(token))
    return {item for item in tokens if item}


def load_json_file(filename: str) -> dict[str, Any]:
    """Load generated JSON data and return an empty dict on failure."""
    path = generated_dir() / filename
    if not path.exists() or not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file_obj:
            value = json.load(file_obj)
            if isinstance(value, dict):
                return value
    except Exception:
        pass
    return {}


def load_context() -> GatewayContext:
    """Load all gateway context sources from AI_BRAIN generated artifacts."""
    return GatewayContext(
        context=load_json_file("context.json"),
        semantic_knowledge=load_json_file("semantic_knowledge.json"),
        relationships=load_json_file("relationships.json"),
        dependency_graph=load_json_file("dependency_graph.json"),
        reasoning_context=load_json_file("reasoning_context.json"),
    )
