#!/usr/bin/env python3
"""Discover converter plugin metadata and generate converters.json."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import generated_dir, parse_python_ast, to_posix_relative, write_json


@dataclass(frozen=True)
class ConverterRecord:
    converter_name: str
    category: str
    source_file: str


def class_inherits_converter(node: ast.ClassDef) -> bool:
    """Return True when class inherits from ConverterPlugin."""
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "ConverterPlugin":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "ConverterPlugin":
            return True
    return False


def discover_converter_names(tree: ast.AST, fallback_name: str) -> list[str]:
    """Discover converter class names from AST."""
    names: list[str] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef) and class_inherits_converter(node):
            names.append(node.name)

    if names:
        return sorted(set(names), key=str.lower)

    return [fallback_name]


def category_from_path(plugin_file: Path, plugins_dir: Path) -> str:
    """Infer converter category from plugin subdirectory."""
    try:
        relative = plugin_file.relative_to(plugins_dir)
    except ValueError:
        return "unknown"

    if len(relative.parts) >= 2:
        return relative.parts[0]
    return "root"


def build_converters(root: Path) -> dict[str, Any]:
    """Build converter metadata from app/plugins directory."""
    plugins_dir = root / "app" / "plugins"
    if not plugins_dir.exists() or not plugins_dir.is_dir():
        return {"totals": {"files_scanned": 0, "converters_discovered": 0}, "converters": []}

    files = sorted(
        [
            path
            for path in plugins_dir.rglob("*.py")
            if path.name != "__init__.py" and path.name != "base.py" and path.name != "registry.py"
        ],
        key=lambda p: str(p).lower(),
    )

    records: list[ConverterRecord] = []

    for file_path in files:
        tree = parse_python_ast(file_path)
        if tree is None:
            continue

        names = discover_converter_names(tree, file_path.stem)
        category = category_from_path(file_path, plugins_dir)
        source_file = to_posix_relative(file_path, root)

        for name in names:
            records.append(
                ConverterRecord(
                    converter_name=name,
                    category=category,
                    source_file=source_file,
                )
            )

    records.sort(key=lambda item: (item.category, item.converter_name.lower(), item.source_file))

    return {
        "totals": {
            "files_scanned": len(files),
            "converters_discovered": len(records),
        },
        "converters": [record.__dict__ for record in records],
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Scan converter plugins and generate converters.json")
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

    converter_data = build_converters(root)
    write_json(output_dir / "converters.json", converter_data)


if __name__ == "__main__":
    main()
