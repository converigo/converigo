#!/usr/bin/env python3
"""Shared helpers for AI_BRAIN semantic engines."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BrainPaths:
    brain_dir: Path
    ai_brain_dir: Path
    generated_dir: Path


@dataclass(frozen=True)
class JsonReadResult:
    name: str
    path: Path
    exists: bool
    data: Any
    error: str | None


def get_brain_paths() -> BrainPaths:
    """Resolve standard AI_BRAIN locations from this module path."""
    brain_dir = Path(__file__).resolve().parent
    ai_brain_dir = brain_dir.parent
    return BrainPaths(brain_dir=brain_dir, ai_brain_dir=ai_brain_dir, generated_dir=ai_brain_dir / "generated")


def load_json(path: Path) -> Any:
    """Load JSON content from path."""
    with path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def read_generated_json(generated_dir: Path, filename: str) -> JsonReadResult:
    """Read generated JSON file with safe error capture."""
    path = generated_dir / filename
    if not path.exists() or not path.is_file():
        return JsonReadResult(name=filename, path=path, exists=False, data=None, error="missing")

    try:
        data = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return JsonReadResult(name=filename, path=path, exists=True, data=None, error=str(exc))

    return JsonReadResult(name=filename, path=path, exists=True, data=data, error=None)


def write_json(path: Path, data: Any) -> None:
    """Write deterministic UTF-8 JSON output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def is_non_empty_str(value: Any) -> bool:
    """Return True if value is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def stem_from_path(path_value: str) -> str:
    """Return stem from a repository-relative path string."""
    return Path(path_value).stem.lower()


def parent_dir_from_path(path_value: str) -> str:
    """Return parent directory from a repository-relative path string."""
    return str(Path(path_value).parent).replace("\\", "/")


def tokenize(value: str) -> set[str]:
    """Create normalized token set for name matching."""
    if not value:
        return set()
    return {token for token in re.split(r"[^a-zA-Z0-9]+", value.lower()) if token}


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    """Compute token-set Jaccard similarity."""
    if not left or not right:
        return 0.0
    intersection = left.intersection(right)
    union = left.union(right)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def normalize_module_name(module_value: str | None) -> str:
    """Normalize import module string for comparisons."""
    if not module_value:
        return ""
    return module_value.strip()
