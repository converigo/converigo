"""Analyze contract files for lifecycle_status."""
import json
from pathlib import Path

d = Path("app/data/converters")
contract_files = sorted([p for p in d.iterdir() if p.suffix == ".json" and p.name.endswith(".contract.json")])
data_files = sorted([p for p in d.iterdir() if p.suffix == ".json" and not p.name.endswith(".contract.json") and not p.name.endswith(".metadata.json")])

print(f"Contract files: {len(contract_files)}")
print(f"Data files: {len(data_files)}")
print()

# Build map from contract lifecycle_status
contract_lifecycle = {}
for f in contract_files:
    data = json.loads(f.read_text(encoding="utf-8"))
    slug = data.get("slug", f.stem.replace(".contract", ""))
    lifecycle = data.get("lifecycle_status", "MISSING")
    contract_lifecycle[slug] = lifecycle
    print(f"  CONTRACT: {slug:30s} lifecycle={lifecycle}")

print()
print("=" * 60)
print()

# Cross-reference with data files
overrides = {
    "mp4-to-mp3": "/mp4-to-mp3",
    "jpg-to-pdf": "/jpg-to-pdf",
    "png-to-jpg": "/png-to-jpg",
    "pdf-to-jpg": "/pdf-to-jpg",
    "png-to-webp": "/png-to-webp",
    "webp-to-png": "/webp-to-png",
}

for f in data_files:
    data = json.loads(f.read_text(encoding="utf-8"))
    slug = data.get("slug", f.stem)
    contract_lc = contract_lifecycle.get(slug, "MISSING_FROM_CONTRACT")
    data_lc = data.get("lifecycle_status", "MISSING")
    
    path = overrides.get(slug, f"/tools/{slug}")
    canonical = f"https://converigo.com{path}"
    
    match = "MATCH" if contract_lc == data_lc or (contract_lc == "MISSING_FROM_CONTRACT" and data_lc == "MISSING") else "MISMATCH"
    print(f"  {slug:30s} | contract_lifecycle={contract_lc:20s} | data_lifecycle={data_lc:20s} | {match:9s} | canonical={canonical}")

