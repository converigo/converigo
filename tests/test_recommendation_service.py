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
        "active": True,
        "source": source or (slug.split("-to-")[0] if "-to-" in slug else "src"),
        "target": target or (slug.split("-to-")[1] if "-to-" in slug else "dst"),
    }
    if related_slugs is not None:
        payload["related_tools"] = [{"slug": related_slug} for related_slug in related_slugs]
    path.write_text(json.dumps(payload), encoding="utf-8")

    # create minimal contract to mark converter as active for tests
    contract = {
        "id": payload["slug"],
        "slug": payload["slug"],
        "name": payload.get("title", payload["slug"]).strip(),
        "category": payload.get("category", "document"),
        "description": payload.get("description", ""),
        "input_formats": [payload["source"]],
        "output_formats": [payload["target"]],
        "accepted_mime_types": ["application/octet-stream"],
        "max_upload_size": 1048576,
        "conversion_engine": "test",
        "landing_path": f"/{payload['slug']}",
        "canonical_url": f"https://converigo.local/{payload['slug']}",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": "ready",
        "regression_sample": str((path.parent / f"{payload['slug']}.sample").resolve()),
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }
    contract_path = path.parent / f"{payload['slug']}.contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    sample_path = path.parent / f"{payload['slug']}.sample"
    if not sample_path.exists():
        sample_path.write_bytes(b"sample")


def test_recommendations_are_deduplicated_and_follow_category_and_workflow(tmp_path: Path) -> None:
    data_dir = tmp_path
    _write_converter(data_dir / "jpg-to-png.json", slug="jpg-to-png", category="image", related_slugs=["png-to-jpg", "webp-to-png"])
    _write_converter(data_dir / "png-to-jpg.json", slug="png-to-jpg", category="image")
    _write_converter(data_dir / "webp-to-png.json", slug="webp-to-png", category="image")
    _write_converter(
        data_dir / "pdf-to-word.json",
        slug="pdf-to-word",
        category="document",
        source="pdf",
        target="docx",
    )
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
    _write_converter(
        data_dir / "new-image-tool.json",
        slug="new-image-tool",
        category="image",
        popular=True,
        source="png",
        target="bmp",
    )

    service = RecommendationService(ConverterDataService(data_dir))
    recommendations = service.recommend_for_slug("jpg-to-png")

    # new-image-tool should appear in recommendations
    all_recommendations = [
        item for group in recommendations.values()
        for item in group
    ]
    assert any(item["slug"] == "new-image-tool" for item in all_recommendations)
    
    # Verify no duplicates across all recommendations
    all_slugs = [item["slug"] for item in all_recommendations]
    assert len(all_slugs) == len(set(all_slugs)), "Duplicate converters found in recommendations"


def test_inactive_converters_do_not_appear_in_recommendations(tmp_path: Path) -> None:
    """Verify that converters without active contracts don't appear in recommendations."""
    data_dir = tmp_path
    _write_converter(data_dir / "pdf-to-word.json", slug="pdf-to-word", category="document")
    
    # Create a converter JSON without contract (inactive)
    inactive_payload = {
        "slug": "inactive-converter",
        "title": "Inactive Converter",
        "description": "This converter has no contract",
        "category": "image",
        "popular": True,
        "source": "jpg",
        "target": "png",
        "active": False,
    }
    (data_dir / "inactive-converter.json").write_text(json.dumps(inactive_payload), encoding="utf-8")
    # Note: deliberately NOT creating a contract file for inactive-converter
    
    service = RecommendationService(ConverterDataService(data_dir))
    recommendations = service.recommend_for_slug("pdf-to-word")
    
    all_slugs = []
    for group in recommendations.values():
        all_slugs.extend(item["slug"] for item in group)
    
    # Inactive converter should never appear
    assert "inactive-converter" not in all_slugs, "Inactive converter appeared in recommendations"


def test_recommendations_do_not_include_duplicate_target_formats(tmp_path: Path) -> None:
    """Verify that when UI extracts target formats, there are no duplicates."""
    data_dir = tmp_path
    _write_converter(data_dir / "pdf-to-word.json", slug="pdf-to-word", category="document", target="docx")
    _write_converter(data_dir / "pdf-to-docx.json", slug="pdf-to-docx", category="document", target="docx")
    _write_converter(data_dir / "docx-to-pdf.json", slug="docx-to-pdf", category="document", source="docx")
    _write_converter(data_dir / "pdf-to-txt.json", slug="pdf-to-txt", category="document", target="txt")
    
    service = RecommendationService(ConverterDataService(data_dir))
    recommendations = service.recommend_for_slug("pdf-to-word")
    
    # Extract all target formats from recommendations
    target_formats = []
    for group in recommendations.values():
        for item in group:
            target_formats.append(item["target"])
    
    # Verify no duplicates in target formats
    assert len(target_formats) == len(set(target_formats)), f"Duplicate target formats found: {target_formats}"


def test_pdf_upload_generates_unique_recommendations(tmp_path: Path) -> None:
    """Regression test: PDF upload should generate unique recommendation list."""
    data_dir = tmp_path
    
    # Simulate typical PDF conversion recommendations
    _write_converter(data_dir / "pdf-to-word.json", slug="pdf-to-word", category="document", source="pdf", target="docx")
    _write_converter(data_dir / "pdf-to-excel.json", slug="pdf-to-excel", category="document", source="pdf", target="xlsx")
    _write_converter(data_dir / "pdf-to-jpg.json", slug="pdf-to-jpg", category="image", source="pdf", target="jpg")
    _write_converter(data_dir / "pdf-to-png.json", slug="pdf-to-png", category="image", source="pdf", target="png")
    
    service = RecommendationService(ConverterDataService(data_dir))
    recommendations = service.recommend_for_slug("pdf-to-word")
    
    # All recommendation items should be unique by slug
    all_items = []
    for group_items in recommendations.values():
        all_items.extend(group_items)
    
    slugs = [item["slug"] for item in all_items]
    assert len(slugs) == len(set(slugs)), f"Duplicate recommendations found: {slugs}"
    
    # All items should have valid conversion metadata
    for item in all_items:
        assert item.get("slug"), "Item missing slug"
        assert item.get("target"), f"Item {item.get('slug')} missing target format"
        assert item.get("reason"), f"Item {item.get('slug')} missing reason"


def test_recommendations_unique_target_formats(tmp_path: Path) -> None:
    """Verify recommendation output contains unique target formats."""
    data_dir = tmp_path

    _write_converter(data_dir / "jpg-to-png.json", slug="jpg-to-png", category="image", source="jpg", target="png", popular=True)
    _write_converter(data_dir / "png-to-jpg.json", slug="png-to-jpg", category="image", source="png", target="jpg", popular=True)
    _write_converter(data_dir / "jpg-to-webp.json", slug="jpg-to-webp", category="image", source="jpg", target="webp", popular=True)
    _write_converter(data_dir / "png-to-webp.json", slug="png-to-webp", category="image", source="png", target="webp", popular=True)
    _write_converter(data_dir / "pdf-to-jpg.json", slug="pdf-to-jpg", category="image", source="pdf", target="jpg", popular=True)
    _write_converter(data_dir / "pdf-to-png.json", slug="pdf-to-png", category="image", source="pdf", target="png", popular=True)
    _write_converter(data_dir / "pdf-to-pdf.json", slug="pdf-to-pdf", category="document", source="pdf", target="pdf", popular=True)
    _write_converter(data_dir / "pdf-to-png-alt.json", slug="pdf-to-png-alt", category="document", source="pdf", target="png", popular=True)

    service = RecommendationService(ConverterDataService(data_dir))

    jpg_recommendations = service.recommend_for_slug("jpg-to-png")
    jpg_targets = [item["target"] for group in jpg_recommendations.values() for item in group]
    assert len(jpg_targets) == len(set(jpg_targets)), f"Duplicate JPG target formats found: {jpg_targets}"

    pdf_recommendations = service.recommend_for_slug("pdf-to-jpg")
    pdf_targets = [item["target"] for group in pdf_recommendations.values() for item in group]
    assert len(pdf_targets) == len(set(pdf_targets)), f"Duplicate PDF target formats found: {pdf_targets}"
