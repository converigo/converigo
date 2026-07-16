import json
from pathlib import Path
import time

from app.services.converter_data_service import ConverterDataService


def _write_converter(
    path: Path,
    slug: str,
    *,
    popular: bool = True,
    featured: bool = False,
    source: str | None = None,
    target: str | None = None,
    sort_order: int | None = None,
) -> None:
    payload = {
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "description": f"{slug} converter",
        "popular": popular,
        "featured": featured,
        "active": True,
        "source": source or (slug.split("-to-")[0] if "-to-" in slug else "src"),
        "target": target or (slug.split("-to-")[1] if "-to-" in slug else "dst"),
    }
    if sort_order is not None:
        payload["sort_order"] = sort_order
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_popular_converters_prioritize_recent_popular_items(tmp_path: Path) -> None:
    service = ConverterDataService(tmp_path)

    for slug in ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]:
        _write_converter(tmp_path / f"{slug}.json", slug)

    newest_slug = "docx-to-pdf"
    _write_converter(
        tmp_path / f"{newest_slug}.json",
        newest_slug,
        source="docx",
        target="pdf",
    )

    # Make the newest converter appear more recent than the others.
    newest_path = tmp_path / f"{newest_slug}.json"
    newer_time = time.time() + 60
    newest_path.touch()
    newest_path.write_text(newest_path.read_text(encoding="utf-8"), encoding="utf-8")
    os_time = time.time()
    if os_time < newer_time:
        pass
    # Use a direct filesystem timestamp update for deterministic ordering.
    import os
    os.utime(newest_path, (newer_time, newer_time))

    result = service.list_popular_converters(limit=6)
    slugs = [converter["slug"] for converter in result]

    assert newest_slug in slugs
    assert slugs[:6] != ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
