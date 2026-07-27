#!/usr/bin/env python3
"""Build high-level project map from repository folder structure."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import default_scan_config, generated_dir, iter_repository_files, to_posix_relative, write_json


CATEGORIES = [
    "Frontend",
    "Backend",
    "Services",
    "Routers",
    "Plugins",
    "Templates",
    "Tests",
    "Static",
    "Configuration",
    "Documentation",
]


@dataclass(frozen=True)
class CategoryRule:
    category: str
    markers: tuple[str, ...]


RULES = [
    CategoryRule("Frontend", ("frontend", "ui", "web", "client", "assets/js", "assets/css")),
    CategoryRule("Backend", ("app", "backend", "api", "server")),
    CategoryRule("Services", ("services",)),
    CategoryRule("Routers", ("routers", "routes")),
    CategoryRule("Plugins", ("plugins", "plugin")),
    CategoryRule("Templates", ("templates", "template")),
    CategoryRule("Tests", ("tests", "test")),
    CategoryRule("Static", ("static", "public", "assets", "uploads")),
    CategoryRule("Configuration", ("config", "configs", "settings")),
    CategoryRule("Documentation", ("docs", "documentation")),
]


def normalize_path(relative_path: str) -> str:
    """Normalize relative path for marker matching."""
    return relative_path.strip("./").lower()


def classify_path(relative_path: str) -> str:
    """Classify a repository path by folder markers only."""
    normalized = normalize_path(relative_path)

    for rule in RULES:
        for marker in rule.markers:
            parts = marker.split("/")
            if all(part in normalized.split("/") for part in parts):
                return rule.category
            if f"/{marker}/" in f"/{normalized}/":
                return rule.category

    return "Backend"


def build_project_map(root: Path) -> dict[str, Any]:
    """Build folder-driven category map for repository files."""
    config = default_scan_config()

    grouped_files: dict[str, list[str]] = {category: [] for category in CATEGORIES}

    for file_path in iter_repository_files(root, config):
        relative_path = to_posix_relative(file_path, root)
        category = classify_path(relative_path)
        if category in grouped_files:
            grouped_files[category].append(relative_path)

    category_summaries: dict[str, Any] = {}
    total_files = 0

    for category in CATEGORIES:
        files = sorted(grouped_files[category])
        folders = sorted({str(Path(path).parent).replace("\\", "/") for path in files})
        category_summaries[category] = {
            "file_count": len(files),
            "folders": folders,
        }
        total_files += len(files)

    return {
        "categories": category_summaries,
        "totals": {
            "files_classified": total_files,
            "categories": len(CATEGORIES),
        },
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Generate project_map.json from folder structure")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--output-dir", type=Path, default=generated_dir(), help="Generated output dir")
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir.resolve()

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Invalid --root directory: {root}")

    project_map = build_project_map(root)
    write_json(output_dir / "project_map.json", project_map)


if __name__ == "__main__":
    main()
