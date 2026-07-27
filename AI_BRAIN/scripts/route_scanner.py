#!/usr/bin/env python3
"""Discover FastAPI routes with Python AST and generate routes.json."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import generated_dir, parse_python_ast, to_posix_relative, write_json

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


@dataclass(frozen=True)
class RouteRecord:
    router: str
    endpoint: str
    http_method: str
    source_file: str


def extract_router_name(call: ast.Call) -> str:
    """Extract router variable name from decorator call."""
    func = call.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name):
            return func.value.id
        if isinstance(func.value, ast.Attribute):
            return ast.unparse(func.value)
    return "unknown"


def extract_endpoint(call: ast.Call) -> str:
    """Extract route endpoint path from decorator call arguments."""
    if call.args:
        first_arg = call.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            return first_arg.value

    for keyword in call.keywords:
        if keyword.arg == "path" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value

    return ""


def routes_from_tree(tree: ast.AST, source_file: str) -> list[RouteRecord]:
    """Extract route metadata from module AST."""
    routes: list[RouteRecord] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue

            method_name = decorator.func.attr.lower()
            if method_name not in HTTP_METHODS:
                continue

            endpoint = extract_endpoint(decorator)
            routes.append(
                RouteRecord(
                    router=extract_router_name(decorator),
                    endpoint=endpoint,
                    http_method=method_name.upper(),
                    source_file=source_file,
                )
            )

    return routes


def build_routes(root: Path) -> dict[str, Any]:
    """Scan app directory for route decorators and return route metadata."""
    app_dir = root / "app"
    if not app_dir.exists() or not app_dir.is_dir():
        return {"totals": {"files_scanned": 0, "routes_discovered": 0}, "routes": []}

    python_files = sorted(app_dir.rglob("*.py"), key=lambda p: str(p).lower())

    records: list[RouteRecord] = []
    for file_path in python_files:
        tree = parse_python_ast(file_path)
        if tree is None:
            continue

        source_file = to_posix_relative(file_path, root)
        records.extend(routes_from_tree(tree, source_file))

    records.sort(key=lambda item: (item.source_file, item.router, item.http_method, item.endpoint))

    return {
        "totals": {
            "files_scanned": len(python_files),
            "routes_discovered": len(records),
        },
        "routes": [record.__dict__ for record in records],
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Discover FastAPI routes and generate routes.json")
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

    route_data = build_routes(root)
    write_json(output_dir / "routes.json", route_data)


if __name__ == "__main__":
    main()
