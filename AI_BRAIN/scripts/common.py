#!/usr/bin/env python3
"""Shared utilities for AI_BRAIN metadata scripts."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    "venv",
    ".venv",
    "node_modules",
    "__pycache__",
    "outputs",
}

DEFAULT_IGNORED_FILES = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
}


@dataclass(frozen=True)
class ScanConfig:
    ignored_directories: set[str]
    ignored_files: set[str]


def default_scan_config() -> ScanConfig:
    """Return default scan configuration for repository walkers."""
    return ScanConfig(
        ignored_directories=set(DEFAULT_IGNORED_DIRECTORIES),
        ignored_files=set(DEFAULT_IGNORED_FILES),
    )


def ai_brain_dir() -> Path:
    """Return AI_BRAIN directory from this script location."""
    return Path(__file__).resolve().parents[1]


def generated_dir() -> Path:
    """Return generated output directory."""
    return ai_brain_dir() / "generated"


def to_posix_relative(path: Path, root: Path) -> str:
    """Return a POSIX-style path relative to root."""
    return path.resolve().relative_to(root.resolve()).as_posix()


def should_skip_dir(path: Path, config: ScanConfig) -> bool:
    """Return True when this directory should be excluded from scans."""
    return path.name in config.ignored_directories


def should_skip_file(path: Path, config: ScanConfig) -> bool:
    """Return True when this file should be excluded from scans."""
    return path.name in config.ignored_files


def iter_repository_files(root: Path, config: ScanConfig) -> Iterator[Path]:
    """Yield all files under root while applying ignore rules."""

    def walk(directory: Path) -> Iterator[Path]:
        for entry in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_dir():
                if should_skip_dir(entry, config):
                    continue
                yield from walk(entry)
            elif entry.is_file():
                if should_skip_file(entry, config):
                    continue
                yield entry

    yield from walk(root)


def load_json(path: Path) -> Any:
    """Load JSON file content."""
    with path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def write_json(path: Path, data: Any) -> None:
    """Write JSON with deterministic formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text and ensure target directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_python_ast(path: Path) -> ast.AST | None:
    """Parse a Python file into AST. Return None on syntax errors."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return None

    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError:
        return None
