import json
from pathlib import Path

from app.services.converter_data_service import ConverterDataService
from app.services.recommendation_service import RecommendationService


def _write_converter(path: Path, *, slug: str, category: str = "image", popular: bool = True, featured: bool = False, source: str | None = None, target: str | None = None, related_slugs: list[str] | None = None) -> None:
    payload = {
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "description": f"{slug} converter",
        "category": category,
        "popular": popular,
        "featured": featured,
        "source": source or slug.split("-to-")[0],
        "target": target or slug.split("-to-")[1] if "-to-" in slug else slug,
    }
    if related_slugs is not None:
        payload["related_tools"] = [{"slug": related_slug} for related_slug in related_slugs]
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_recommendations_are_deduplicated_and_follow_category_and_workflow(tmp_path: Path) -> None:
    data_dir = tmp_path
    _write_converter(data_dir / "jpg-to-png.json", slug="jpg-to-png", category="image", related_slugs=["png-to-jpg", "webp-to-png"])
    _write_converter(data_dir / "png-to-jpg.json", slug="png-to-jpg", category="image")
    _write_converter(data_dir / "webp-to-png.json", slug="webp-to-png", category="image")
    _write_converter(data_dir / "pdf-to-word.json", slug="pdf-to-word", category="document")
    _write_converter(data_dir / "jpg-to-webp.json", slug="jpg-to-webp", category="image")

    service = RecommendationService(ConverterDataService(data_dir))
    recommendations = service.recommend_for_slug("jpg-to-png")

    all_slugs = []
    for group in recommendations.values():
        all_slugs.extend(item["slug"] for item in group)

    assert len(all_slugs) == len(set(all_slugs))
    assert "png-to-jpg" in [item["slug"] for item in recommendations["related_converters"]]
    assert any(item["slug"] == "jpg-to-webp" for item in recommendations["same_category_converters"])
    assert any(
        item["slug"] not in {None, ""} and item["slug"] != "jpg-to-png"
        for item in recommendations["workflow_recommendations"]
    )


def test_new_converter_is_included_without_manual_configuration(tmp_path: Path) -> None:
    data_dir = tmp_path
    _write_converter(data_dir / "jpg-to-png.json", slug="jpg-to-png", category="image", related_slugs=[])
    _write_converter(data_dir / "png-to-jpg.json", slug="png-to-jpg", category="image")
    _write_converter(data_dir / "new-image-tool.json", slug="new-image-tool", category="image", popular=True)

    service = RecommendationService(ConverterDataService(data_dir))
    recommendations = service.recommend_for_slug("jpg-to-png")

    assert any(item["slug"] == "new-image-tool" for item in recommendations["same_category_converters"])
    assert any(item["slug"] == "new-image-tool" for item in recommendations["popular_converters"])
