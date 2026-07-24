#!/usr/bin/env python3
"""Scan app/services and generate services.json metadata."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import generated_dir, parse_python_ast, to_posix_relative, write_json


@dataclass(frozen=True)
class ServiceRecord:
    service_name: str
    source_file: str
    public_methods: list[str]


def public_method_names_from_class(node: ast.ClassDef) -> list[str]:
    """Return public method names from class definition."""
    methods: list[str] = []

    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not item.name.startswith("_"):
                methods.append(item.name)

    return sorted(set(methods), key=str.lower)


def public_top_level_functions(tree: ast.AST) -> list[str]:
    """Return public top-level function names from module AST."""
    names: list[str] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            names.append(node.name)

    return sorted(set(names), key=str.lower)


def service_records_for_file(tree: ast.AST, source_file: str, fallback_name: str) -> list[ServiceRecord]:
    """Create service records from class and module metadata."""
    class_records: list[ServiceRecord] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            class_records.append(
                ServiceRecord(
                    service_name=node.name,
                    source_file=source_file,
                    public_methods=public_method_names_from_class(node),
                )
            )

    if class_records:
        return class_records

    return [
        ServiceRecord(
            service_name=fallback_name,
            source_file=source_file,
            public_methods=public_top_level_functions(tree),
        )
    ]


def build_services(root: Path) -> dict[str, Any]:
    """Build services metadata from app/services Python files."""
    services_dir = root / "app" / "services"
    if not services_dir.exists() or not services_dir.is_dir():
        return {"totals": {"files_scanned": 0, "services_discovered": 0}, "services": []}

    files = sorted(
        [path for path in services_dir.rglob("*.py") if path.name != "__init__.py"],
        key=lambda p: str(p).lower(),
    )

    records: list[ServiceRecord] = []
    for file_path in files:
        tree = parse_python_ast(file_path)
        if tree is None:
            continue

        source_file = to_posix_relative(file_path, root)
        fallback_name = file_path.stem
        records.extend(service_records_for_file(tree, source_file, fallback_name))

    records.sort(key=lambda item: (item.source_file, item.service_name.lower()))

    return {
        "totals": {
            "files_scanned": len(files),
            "services_discovered": len(records),
        },
        "services": [record.__dict__ for record in records],
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Scan app/services and generate services.json")
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

    services_data = build_services(root)
    write_json(output_dir / "services.json", services_data)


if __name__ == "__main__":
    main()
