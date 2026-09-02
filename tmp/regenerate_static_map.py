"""
regenerate_static_map.py — Bangun ulang STATIC_TARGET_MAP dari registry
yang sudah menerapkan FIX 1 (filter supports() aktif).

Aturan:
1. Ambil semua source dari registry.plugins (FIX 1 sudah filter).
2. Untuk setiap source, kumpulkan semua target yang terdaftar.
3. Hapus self-conversion (source.lower() === target.lower()).
4. Hapus alias format variant (jpg↔jpeg, gz↔gzip) — kontrak map.
5. Pertahankan key yang sudah ada (termasuk yang array kosong) untuk
   format yang tidak ada di registry (html, md, rtf, wav, ogg, dll).
6. Output sebagai JavaScript object literal.
"""

import sys
from collections import defaultdict

# Ensure project root is importable when run as a plain script
sys.path.insert(0, r"C:\converigo")

# Alias groups: variants of the same format that should be treated
# as self-conversions for the dropdown map.
ALIAS_GROUPS = {
    frozenset({"jpg", "jpeg"}),
    frozenset({"gz", "gzip"}),
}


def _alias_group(fmt: str) -> frozenset | None:
    """Return the alias group containing fmt, or None if fmt is not in any group."""
    for group in ALIAS_GROUPS:
        if fmt in group:
            return group
    return None


def _is_self_or_alias(source: str, target: str) -> bool:
    """Return True if target is a self-conversion or alias variant of source."""
    if source.lower() == target.lower():
        return True
    group = _alias_group(source.lower())
    if group and target.lower() in group:
        return True
    return False


def build_map_from_registry(registry) -> dict[str, list[str]]:
    """Build STATIC_TARGET_MAP from the registry.

    Returns dict of source_lower -> sorted list of UPPERCASE target strings.
    """
    source_targets = defaultdict(set)

    for (src, tgt) in registry.plugins:
        source_targets[src].add(tgt)

    result = {}
    for src in sorted(source_targets):
        targets = sorted(source_targets[src])
        # Remove self-conversions and alias variants
        filtered = [t.upper() for t in targets if not _is_self_or_alias(src, t)]
        result[src] = filtered

    return result


def format_js_map(reg_map: dict[str, list[str]], existing_keys: set[str]) -> str:
    """Format the map as a JavaScript object literal.

    - reg_map: map from registry (source -> [targets])
    - existing_keys: all keys that should appear in the output
      (including empty-array keys like html, md, rtf, etc.)
    """
    lines = []
    lines.append("const STATIC_TARGET_MAP = {")

    # Group keys by category for readability (matching the current format)
    # We'll just output alphabetically for simplicity, but group comments help.
    all_keys = sorted(existing_keys)

    for key in all_keys:
        targets = reg_map.get(key, [])
        if targets:
            targets_str = "','".join(targets)
            lines.append(f"  {key}:['{targets_str}'],")
        else:
            lines.append(f"  {key}:[],")

    lines.append("};")
    return "\n".join(lines)


if __name__ == "__main__":
    # Load registry (FIX 1 active)
    from app.plugins.registry import registry

    # Build map from registry
    reg_map = build_map_from_registry(registry)

    # Existing keys to preserve (from the current STATIC_TARGET_MAP)
    # These are all keys that should appear in the output.
    # Sourced from the current map in converigo_main.html.
    existing_keys = {
        "jpg", "jpeg", "png", "webp", "bmp", "tiff", "svg", "gif",
        "heic", "heif", "avif",
        "pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "txt",
        "csv", "ods", "odt", "html", "md", "rtf",
        "mp3", "wav", "ogg", "flac", "m4a", "aac",
        "mp4", "mov", "avi", "webm", "mkv", "flv",
        "gz", "gzip", "zip", "7z", "rar", "tar",
        "powerpoint", "spreadsheet", "word",
    }

    js = format_js_map(reg_map, existing_keys)
    print(js)

    # Also print a human-readable summary for verification
    print("\n/* --- Human-readable summary --- */", file=sys.stderr)
    for key in sorted(reg_map):
        targets = reg_map[key]
        if targets:
            print(f"  {key}: {targets}", file=sys.stderr)
        else:
            print(f"  {key}: [] (no targets after filter)", file=sys.stderr)
    print(file=sys.stderr)