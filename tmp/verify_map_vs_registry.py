"""verify_map_vs_registry.py — Verify the deployed STATIC_TARGET_MAP in
converigo_main.html exactly matches the FIX 1 registry derivation.

Comparison:
1. Deployed map: parsed from the HTML via Node (JSON dump of STATIC_TARGET_MAP).
2. Registry map: built from registry.plugins (FIX 1 supports() filter active)
   using the exact same self/alias removal rules as regenerate_static_map.py.
"""
import json
import re
import subprocess
import sys

WORKTREE_ROOT = r"C:\converigo\wt_batch3"
sys.path.insert(0, WORKTREE_ROOT)

from app.plugins.registry import registry  # noqa: E402
sys.path.insert(0, WORKTREE_ROOT + r"\tmp")
import regenerate_static_map as gen  # noqa: E402

HTML_PATH = WORKTREE_ROOT + r"\app\templates\main\converigo_main.html"

# 1) Extract deployed map via Node (handles JS comments / quoting correctly)
node_snippet = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const m = html.match(/const STATIC_TARGET_MAP = \{([\s\S]*?)\};/);
if (!m) { console.error('STATIC_TARGET_MAP not found'); process.exit(1); }
const mapSrc = 'globalThis.STATIC_TARGET_MAP = {' + m[1] + '};';
(0, eval)(mapSrc);
console.log(JSON.stringify(globalThis.STATIC_TARGET_MAP));
"""
proc = subprocess.run(
    ["node", "-e", node_snippet, HTML_PATH],
    capture_output=True, text=True, encoding="utf-8",
)
if proc.returncode != 0:
    print("NODE ERROR:", proc.stderr)
    sys.exit(1)
html_map = json.loads(proc.stdout.strip())

# 2) Registry-derived map (FIX 1)
reg_map = gen.build_map_from_registry(registry)

# 3) Compare on the union of keys
all_keys = sorted(set(html_map) | set(reg_map))
missing = [k for k in reg_map if k not in html_map]
extra = [k for k in html_map if k not in reg_map]
mismatch = {
    k: (html_map.get(k), reg_map.get(k))
    for k in all_keys
    if html_map.get(k) != reg_map.get(k)
}

print(f"deployed_keys={len(html_map)}  registry_sources={len(reg_map)}")
print(f"registry_sources_missing_from_html: {missing or 'NONE'}")
print(f"html_keys_not_in_registry_sources: {extra or 'NONE'}")
if mismatch:
    print("MISMATCHES:")
    for k, (a, b) in sorted(mismatch.items()):
        print(f"  {k}: html={a}  registry={b}")
else:
    print("MATCH: deployed map == FIX 1 registry derivation for ALL keys.")

# 4) Also print the registry non-empty targets for human review
print("\n--- Registry-derived non-empty targets ---")
for k in sorted(reg_map):
    if reg_map[k]:
        print(f"  {k}: {reg_map[k]}")
