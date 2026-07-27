"""Fix canonical URLs to use correct routing paths (not contract canonical_url which omits /tools/)."""
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

fixed = 0
for f in data_files:
    data = json.loads(f.read_text(encoding="utf-8"))
    slug = data.get("slug", f.stem)
    seo = data.get("seo", {})
    
    path = LANDING_PAGE_OVERRIDES.get(slug, f"/tools/{slug}")
    expected = f"{BASE_URL.rstrip('/')}{path}"
    
    if seo.get("canonical") != expected:
        seo["canonical"] = expected
        data["seo"] = seo
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        fixed += 1
        print(f"  ✓ Fixed {slug:30s} -> {expected}")

print(f"\nFixed {fixed} canonical URLs")

