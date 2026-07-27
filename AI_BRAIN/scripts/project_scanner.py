#!/usr/bin/env python3
"""Project scanner for Converigo AI Brain.

Scans a repository, excludes configured directories, and generates:
- project_index.json
- file_tree.json
- import_map.json

Collected file metadata is limited to:
- path
- extension
- size
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import (
    default_scan_config,
    generated_dir,
    iter_repository_files,
    parse_python_ast,
    to_posix_relative,
    write_json,
)


@dataclass(frozen=True)
class FileMetadata:
    path: str
    extension: str
    size: int


@dataclass(frozen=True)
class ImportRecord:
    type: str
    source_file: str
    module: str | None
    import_name: str | None
    alias: str | None


def file_metadata(path: Path, root: Path) -> FileMetadata:
    """Build metadata for a file without reading its content."""
    return FileMetadata(
        path=to_posix_relative(path, root),
        extension=path.suffix.lower(),
        size=path.stat().st_size,
    )


def build_project_index(root: Path) -> list[dict[str, Any]]:
    """Return a flat, sorted list of file metadata for the repository."""
    config = default_scan_config()
    entries = [file_metadata(path, root) for path in iter_repository_files(root, config)]
    entries.sort(key=lambda item: item.path)
    return [entry.__dict__ for entry in entries]


def build_file_tree(root: Path) -> dict[str, Any]:
    """Return a nested file tree with directory and file metadata."""
    config = default_scan_config()

    def node_for_directory(directory: Path) -> dict[str, Any]:
        children: list[dict[str, Any]] = []

        for entry in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_dir():
                if entry.name in config.ignored_directories:
                    continue
                children.append(node_for_directory(entry))
            elif entry.is_file():
                if entry.name in config.ignored_files:
                    continue
                metadata = file_metadata(entry, root)
                children.append(
                    {
                        "type": "file",
                        "path": metadata.path,
                        "extension": metadata.extension,
                        "size": metadata.size,
                    }
                )

        return {
            "type": "directory",
            "path": to_posix_relative(directory, root) if directory != root else ".",
            "children": children,
        }

    return node_for_directory(root)


def import_records_for_file(path: Path, root: Path) -> list[ImportRecord]:
    """Extract import metadata from a Python file using AST."""
    tree = parse_python_ast(path)
    if tree is None:
        return []

    source_file = to_posix_relative(path, root)
    records: list[ImportRecord] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                records.append(
                    ImportRecord(
                        type="import",
                        source_file=source_file,
                        module=alias.name,
                        import_name=None,
                        alias=alias.asname,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            if node.level > 0:
                prefix = "." * node.level
                module_name = f"{prefix}{module_name}" if module_name else prefix
            for alias in node.names:
                records.append(
                    ImportRecord(
                        type="from_import",
                        source_file=source_file,
                        module=module_name,
                        import_name=alias.name,
                        alias=alias.asname,
                    )
                )

    return records


def build_import_map(root: Path) -> dict[str, Any]:
    """Build AST-derived import metadata for Python files in the repository."""
    config = default_scan_config()
    files = [path for path in iter_repository_files(root, config) if path.suffix.lower() == ".py"]

    records: list[ImportRecord] = []
    for file_path in files:
        records.extend(import_records_for_file(file_path, root))

    records.sort(key=lambda item: (item.source_file, item.type, item.module or "", item.import_name or ""))

    return {
        "totals": {
            "python_files_scanned": len(files),
            "imports_discovered": len(records),
        },
        "imports": [record.__dict__ for record in records],
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Scan repository and generate metadata index files.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to scan (default: current working directory).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=generated_dir(),
        help="Directory where JSON outputs are written (default: AI_BRAIN/generated).",
    )
    return parser.parse_args()


def main() -> None:
    """Execute repository scan and generate output files."""
    args = parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir.resolve()

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Invalid --root directory: {root}")

    project_index = build_project_index(root)
    file_tree = build_file_tree(root)
    import_map = build_import_map(root)

    write_json(output_dir / "project_index.json", project_index)
    write_json(output_dir / "file_tree.json", file_tree)
    write_json(output_dir / "import_map.json", import_map)


if __name__ == "__main__":
    main()
