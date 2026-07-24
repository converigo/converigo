"""Verify canonical URLs in data files match expected routing paths."""
import json
from pathlib import Path

d = Path("app/data/converters")

# Converters with dedicated landing page routes (not under /tools/)
LANDING_PAGE_OVERRIDES = {
    "mp4-to-mp3": "/mp4-to-mp3",
    "jpg-to-pdf": "/jpg-to-pdf",
    "png-to-jpg": "/png-to-jpg",
    "pdf-to-jpg": "/pdf-to-jpg",
    "png-to-webp": "/png-to-webp",
    "webp-to-png": "/webp-to-png",
}

BASE_URL = "https://converigo.com"

data_files = sorted([
    p for p in d.iterdir()
    if p.suffix == ".json"
    and not p.name.endswith(".contract.json")
    and not p.name.endswith(".metadata.json")
])

mismatches = []
ok = []
missing = []

for f in data_files:
    data = json.loads(f.read_text(encoding="utf-8"))
    slug = data.get("slug", f.stem)
    seo = data.get("seo", {})
    canonical = seo.get("canonical", "")
    
    path = LANDING_PAGE_OVERRIDES.get(slug, f"/tools/{slug}")
    expected = f"{BASE_URL.rstrip('/')}{path}"
    
    if not canonical:
        missing.append(slug)
    elif canonical == expected:
        ok.append((slug, canonical))
    else:
        mismatches.append((slug, canonical, expected))

print(f"Verified {len(data_files)} data files")
print()

print(f"OK ({len(ok)}):")
for slug, canon in ok:
    print(f"  ✓ {slug:30s} -> {canon}")

if mismatches:
    print(f"\nMISMATCHES ({len(mismatches)}):")
    for slug, canon, expected in mismatches:
        print(f"  ✗ {slug:30s} has={canon:50s} expected={expected}")

if missing:
    print(f"\nMISSING ({len(missing)}):")
    for s in missing:
        print(f"  - {s}")

print()
print(f"Total: {len(data_files)}, OK: {len(ok)}, Mismatches: {len(mismatches)}, Missing: {len(missing)}")

