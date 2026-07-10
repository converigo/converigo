"""
List plugins and supported pairs using the registry.

Usage:
    python scripts/list_plugins.py
"""
from app.plugins.registry import registry

pairs = []
for (s, t), plugin in registry.plugins.items():
    pairs.append((s, t, plugin.slug))

pairs_sorted = sorted(set(pairs))
for s, t, slug in pairs_sorted:
    print(f"{s} -> {t}  ({slug})")
