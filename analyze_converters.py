"""Analyze converter JSON files for lifecycle and canonical status."""
import json
from pathlib import Path

d = Path("app/data/converters")
files = [p for p in d.iterdir() if p.suffix == ".json" and not p.name.endswith(".contract.json") and not p.name.endswith(".metadata.json")]
files.sort()

print(f"Total converter JSON files: {len(files)}")
print()

no_lifecycle = []
no_canonical = []
have_canonical = []

for f in files:
    data = json.loads(f.read_text(encoding="utf-8"))
    slug = data.get("slug", f.stem)
    seo = data.get("seo", {})
    lifecycle = data.get("lifecycle_status", data.get("status", "MISSING"))
    canonical = seo.get("canonical", "MISSING")
    
    if lifecycle == "MISSING":
        no_lifecycle.append(slug)
    if canonical == "MISSING":
        no_canonical.append(slug)
    else:
        have_canonical.append((slug, canonical))
    
    status = "OK" if lifecycle != "MISSING" and canonical != "MISSING" else "NEEDS FIX"
    print(f"  {status:10s} | {slug:30s} | lifecycle={lifecycle:15s} | canonical={canonical}")

print()
print(f"Missing lifecycle_status: {len(no_lifecycle)}")
for s in no_lifecycle:
    print(f"  - {s}")

print()
print(f"Missing canonical: {len(no_canonical)}")
for s in no_canonical:
    print(f"  - {s}")

print()
print(f"Have canonical ({len(have_canonical)}):")
for slug, canon in have_canonical:
    print(f"  - {slug:30s} -> {canon}")

