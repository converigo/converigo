from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.plugins import discover_plugins


def main() -> int:
    result = discover_plugins()

    print("=" * 60)
    print("PLUGIN IMPORT VERIFICATION")
    print("=" * 60)

    for plugin_class in result.plugin_classes:
        print(f"Loaded Plugin: {plugin_class.__module__}.{plugin_class.__name__}")

    for item in result.skipped_plugins:
        print(f"Skipped Plugin: {item.module_name} | Reason: {item.reason}")

    print("=" * 60)
    print(f"Loaded Plugin Count: {len(result.plugin_classes)}")
    print(f"Skipped Plugin Count: {len(result.skipped_plugins)}")
    print("=" * 60)

    return 1 if result.skipped_plugins else 0


if __name__ == "__main__":
    raise SystemExit(main())